"""Fenêtre « Votre journée » : briefing à l'ouverture de session."""
from __future__ import annotations

from datetime import date

from gi.repository import Adw, GLib, Gtk

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
CSS = """
.indicateur { padding: 12px 16px; }
.indicateur .valeur { font-size: 22pt; font-weight: 800; }
.synthese { padding: 16px 18px; }
"""


def date_longue(jour: date) -> str:
    return f"{JOURS[jour.weekday()]} {jour.day} {MOIS[jour.month - 1]} {jour.year}"


def relative(jour: date, reference: date) -> str:
    ecart = (jour - reference).days
    if ecart < 0:
        return f"en retard de {-ecart} jour{'s' if ecart < -1 else ''}"
    return {0: "aujourd'hui", 1: "demain"}.get(ecart, f"dans {ecart} jours")


class FenetreBriefing(Adw.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="Votre journée", default_width=780, default_height=880)
        self.application = application
        self.set_hide_on_close(True)
        style = Gtk.CssProvider()
        style.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(self.get_display(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        vue = Adw.ToolbarView()
        entete = Adw.HeaderBar()
        actualiser = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Actualiser")
        actualiser.connect("clicked", lambda *_: application.actualiser())
        entete.pack_end(actualiser)
        vue.add_top_bar(entete)
        self.banniere = Adw.Banner()
        vue.add_top_bar(self.banniere)

        defilement = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.cadre = Adw.Clamp(maximum_size=740)
        defilement.set_child(self.cadre)
        vue.set_content(defilement)

        boutons = Gtk.Box(spacing=12, halign=Gtk.Align.END, margin_top=12, margin_bottom=12,
                          margin_start=18, margin_end=18)
        commencer = Gtk.Button(label="Commencer la journée")
        commencer.add_css_class("pill")
        commencer.connect("clicked", lambda *_: self.close())
        ouvrir_ia = Gtk.Button(label=f"Ouvrir {application.config.nom}")
        ouvrir_ia.add_css_class("pill")
        ouvrir_ia.add_css_class("suggested-action")
        ouvrir_ia.connect("clicked", lambda *_: application.montrer_panneau())
        boutons.append(commencer)
        boutons.append(ouvrir_ia)
        vue.add_bottom_bar(boutons)
        self.set_content(vue)
        self._attente()

    def _attente(self):
        boite = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, valign=Gtk.Align.CENTER, margin_top=120)
        boite.append(Adw.Spinner(width_request=48, height_request=48))
        boite.append(Gtk.Label(label="Préparation de votre journée…"))
        self.cadre.set_child(boite)

    def afficher(self, briefing) -> None:
        racine = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24, margin_top=24, margin_bottom=24,
                         margin_start=18, margin_end=18)
        prenom = (GLib.get_real_name() or "").split(" ")[0]
        bonjour = Gtk.Label(label=f"Bonjour {prenom}" if prenom and prenom != "Unknown" else "Bonjour", xalign=0)
        bonjour.add_css_class("title-1")
        jour = Gtk.Label(label=date_longue(briefing.jour).capitalize(), xalign=0)
        jour.add_css_class("dim-label")
        en_tete = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        en_tete.append(bonjour)
        en_tete.append(jour)
        racine.append(en_tete)

        # Un message court et lisible : le détail technique reste dans « poste-ia briefing-texte ».
        self.banniere.set_title(" · ".join(
            f"{source} : {raison if len(raison) <= 40 else 'indisponible'}"
            for source, raison in briefing.indisponibles.items()))
        self.banniere.set_revealed(bool(briefing.indisponibles))

        synthese = Gtk.Label(label=briefing.resume(), wrap=True, xalign=0, selectable=True)
        synthese.add_css_class("card")
        synthese.add_css_class("synthese")
        racine.append(synthese)

        indicateurs = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                                  min_children_per_line=2, max_children_per_line=4,
                                  column_spacing=12, row_spacing=12)
        for libelle, valeur in briefing.vue_globale():
            carte = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            carte.add_css_class("card")
            carte.add_css_class("indicateur")
            chiffre = Gtk.Label(label=valeur, xalign=0)
            chiffre.add_css_class("valeur")
            nom = Gtk.Label(label=libelle, xalign=0, wrap=True)
            nom.add_css_class("dim-label")
            carte.append(chiffre)
            carte.append(nom)
            indicateurs.append(carte)
        racine.append(indicateurs)

        reference = briefing.jour
        racine.append(self._groupe("Rendez-vous", briefing.rendez_vous, self._ligne_rdv, "Aucun rendez-vous"))
        taches = self._groupe("À faire", briefing.a_faire, lambda e: self._ligne_tache(e, reference), "Rien à faire")
        ajout = Adw.EntryRow(title="Ajouter une tâche", show_apply_button=True)
        ajout.connect("apply", self._ajouter_tache)
        taches.add(ajout)
        racine.append(taches)
        racine.append(self._groupe("Points à vérifier", briefing.a_verifier, self._ligne_verifier, "Rien à vérifier"))
        racine.append(self._groupe("Échéances", briefing.echeances, lambda e: self._ligne_echeance(e, reference),
                                   "Aucune échéance dans les 7 jours"))
        self.cadre.set_child(racine)

    def _groupe(self, titre, elements, rendu, vide):
        groupe = Adw.PreferencesGroup(title=titre)
        if not elements:
            ligne = Adw.ActionRow(title=vide)
            ligne.add_css_class("dim-label")
            groupe.add(ligne)
        for element in elements:
            groupe.add(rendu(element))
        return groupe

    @staticmethod
    def _sous_titre(*parties):
        return GLib.markup_escape_text(" · ".join(p for p in parties if p))

    def _ligne(self, element, sous_titre, icone=None):
        ligne = Adw.ActionRow(title=GLib.markup_escape_text(element.titre), subtitle=sous_titre)
        if icone:
            ligne.add_prefix(Gtk.Image(icon_name=icone))
        if element.priorite == "haute":
            marque = Gtk.Label(label="prioritaire", valign=Gtk.Align.CENTER)
            marque.add_css_class("warning")
            ligne.add_suffix(marque)
        if element.lien:
            ligne.set_activatable(True)
            ligne.connect("activated", lambda *_: Gtk.UriLauncher.new(element.lien).launch(self, None, None, None))
        return ligne

    def _ligne_rdv(self, element):
        horaire = f"{element.debut:%H:%M}" if element.debut else "Journée"
        if element.debut and element.fin:
            horaire += f" – {element.fin:%H:%M}"
        return self._ligne(element, self._sous_titre(horaire, element.detail), "x-office-calendar-symbolic")

    def _ligne_tache(self, element, reference):
        echeance = relative(element.echeance, reference) if element.echeance else ""
        ligne = self._ligne(element, self._sous_titre(echeance, element.detail, element.source))
        case = Gtk.CheckButton(active=element.fait, valign=Gtk.Align.CENTER, sensitive=element.modifiable)
        if element.modifiable:
            case.connect("toggled", lambda bouton: self.application.basculer_tache(element.ident, bouton.get_active()))
        ligne.add_prefix(case)
        return ligne

    def _ligne_verifier(self, element):
        return self._ligne(element, self._sous_titre(element.detail, element.source), "dialog-warning-symbolic")

    def _ligne_echeance(self, element, reference):
        quand = relative(element.echeance, reference) if element.echeance else ""
        return self._ligne(element, self._sous_titre(quand, element.detail, element.source), "alarm-symbolic")

    def _ajouter_tache(self, ligne):
        titre = ligne.get_text().strip()
        if titre:
            self.application.ajouter_tache(titre)
            ligne.set_text("")
