"""Panneau de l'IA métier (Super+Espace) : conversation, journal, arrêt d'urgence."""
from __future__ import annotations

import threading

from gi.repository import Adw, Gio, GLib, Gtk

from ..permissions import arret_actif
from ..sources.connecteur import ConnecteurIndisponible
from .journal import FenetreJournal

CSS = """
.bulle, .bulle-moi { padding: 8px 12px; }
.bulle-moi { background-color: alpha(@accent_bg_color, 0.14); }
"""


class Panneau(Adw.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title=application.config.nom,
                         default_width=440, default_height=720)
        self.application = application
        self.historique: list[dict] = []
        self.set_hide_on_close(True)

        for nom, rappel in (("journal", self._journal), ("arret", self._basculer_arret)):
            action = Gio.SimpleAction.new(nom, None)
            action.connect("activate", rappel)
            self.add_action(action)
        menu = Gio.Menu()
        menu.append("Briefing du jour", "app.briefing")
        menu.append("Journal des actions de l'IA", "win.journal")
        menu.append("Arrêt d'urgence / reprise", "win.arret")

        vue = Adw.ToolbarView()
        entete = Adw.HeaderBar()
        entete.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu))
        vue.add_top_bar(entete)
        self.etat = Adw.Banner()
        self.etat.connect("button-clicked", self._basculer_arret)
        vue.add_top_bar(self.etat)

        self.messages = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_top=12,
                                margin_bottom=12, margin_start=12, margin_end=12)
        self.defilement = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER,
                                             child=self.messages)
        vue.set_content(self.defilement)

        saisie = Gtk.Box(spacing=8, margin_top=8, margin_bottom=12, margin_start=12, margin_end=12)
        self.entree = Gtk.Entry(hexpand=True, placeholder_text="Posez votre question…")
        self.entree.connect("activate", self._envoyer)
        envoyer = Gtk.Button(icon_name="mail-send-symbolic", tooltip_text="Envoyer")
        envoyer.add_css_class("suggested-action")
        envoyer.add_css_class("circular")
        envoyer.connect("clicked", self._envoyer)
        saisie.append(self.entree)
        saisie.append(envoyer)
        vue.add_bottom_bar(saisie)
        self.set_content(vue)

        style = Gtk.CssProvider()
        style.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(self.get_display(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._bulle(f"Bonjour, je suis {application.config.nom}. Que puis-je faire pour vous ?", "ia")
        self.maj_etat()
        # Le curseur dans la zone de saisie (sinon le premier message serait sélectionné).
        self.entree.grab_focus()

    def maj_etat(self) -> None:
        if arret_actif(self.application.config):
            self.etat.set_title("Arrêt d'urgence actif : l'IA n'agit plus sur ce poste.")
            self.etat.set_button_label("Reprendre")
            self.etat.set_revealed(True)
        elif not self.application.connecteur.actif:
            self.etat.set_title(f"{self.application.config.nom} n'est pas encore connectée à ce poste.")
            self.etat.set_button_label(None)
            self.etat.set_revealed(True)
        else:
            self.etat.set_revealed(False)

    def _bulle(self, texte: str, auteur: str) -> Gtk.Label:
        texte_bulle = Gtk.Label(label=texte, wrap=True, xalign=0, selectable=True, max_width_chars=46)
        cadre = Gtk.Box(halign=Gtk.Align.END if auteur == "moi" else Gtk.Align.START)
        cadre.add_css_class("card")
        cadre.add_css_class("bulle-moi" if auteur == "moi" else "bulle")
        cadre.set_margin_start(36 if auteur == "moi" else 0)
        cadre.set_margin_end(0 if auteur == "moi" else 36)
        if auteur == "systeme":
            texte_bulle.add_css_class("dim-label")
        cadre.append(texte_bulle)
        self.messages.append(cadre)
        GLib.idle_add(self._defiler_en_bas)
        return texte_bulle

    def _defiler_en_bas(self):
        reglage = self.defilement.get_vadjustment()
        reglage.set_value(reglage.get_upper())
        return False

    def demander(self, texte: str) -> None:
        self.entree.set_text(texte)
        self._envoyer()

    def _envoyer(self, *_):
        texte = self.entree.get_text().strip()
        if not texte:
            return
        self.entree.set_text("")
        self._bulle(texte, "moi")
        if not self.application.connecteur.actif:
            self._bulle(f"{self.application.config.nom} n'est pas encore connectée à ce poste : "
                        "votre demande n'a pas été envoyée.", "systeme")
            return
        self.historique.append({"role": "user", "content": texte})
        reponse = self._bulle("…", "ia")
        self.entree.set_sensitive(False)
        threading.Thread(target=self._converser, args=(reponse,), daemon=True).start()

    def _converser(self, reponse: Gtk.Label) -> None:
        morceaux: list[str] = []
        try:
            for delta in self.application.connecteur.converser(self.historique):
                morceaux.append(delta)
                GLib.idle_add(reponse.set_text, "".join(morceaux))
            final = "".join(morceaux) or "(réponse vide)"
            self.historique.append({"role": "assistant", "content": final})
            GLib.idle_add(reponse.set_text, final)
        except ConnecteurIndisponible as erreur:
            GLib.idle_add(reponse.set_text, f"Connexion impossible : {erreur}")
        finally:
            GLib.idle_add(self.entree.set_sensitive, True)
            GLib.idle_add(self._defiler_en_bas)

    def _journal(self, *_):
        FenetreJournal(self, self.application.journal).present()

    def _basculer_arret(self, *_):
        self.application.basculer_arret()
        self.maj_etat()
