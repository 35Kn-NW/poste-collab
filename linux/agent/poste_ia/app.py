"""Application GNOME de l'agent : une seule instance par session (briefing, panneau, recherche, rappels)."""
from __future__ import annotations

import threading
import time
from datetime import date, datetime

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib  # noqa: E402

from . import APP_ID  # noqa: E402
from .config import charger  # noqa: E402
from .etat import Sondes, publier  # noqa: E402
from .journal import Journal  # noqa: E402
from .outils import Moteur  # noqa: E402
from .permissions import ArretUrgence, Refus, activer_arret, arret_actif, lever_arret  # noqa: E402
from .recherche import FournisseurRecherche  # noqa: E402
from .sources import construire, enregistrer_cache, lire_cache  # noqa: E402
from .sources.connecteur import Connecteur, ConnecteurIndisponible  # noqa: E402
from .sources.evolution import AgendaEvolution  # noqa: E402
from .sources.ia import SourceIA  # noqa: E402
from .sources.locale import TachesLocales  # noqa: E402

DEMANDES = {
    "resumer": "Résume ce document : {}",
    "verifier": "Vérifie cet acte et liste les points à contrôler : {}",
    "repondre": "Prépare un brouillon de réponse au client à partir de : {}",
    "sceller": "Scelle ce document dans le registre d'horodatage : {}",
}
ACTUALISATION_MINUTES = 30


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.config = charger()
        self.journal = Journal(self.config.dossier_etat)
        self.connecteur = Connecteur(self.config)
        self.taches = TachesLocales(self.config.dossier_donnees)
        self.moteur = Moteur(self.config, self.journal, notifier=self.notifier, connecteur=self.connecteur)
        self.briefing = lire_cache(self.config.dossier_donnees, date.today())
        self.recherche = FournisseurRecherche(self)
        self.fenetre_briefing = None
        self.panneau = None
        self._rappels_faits: set[str] = set()
        self._minutes = 0

    # --- Cycle de vie -------------------------------------------------------

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.hold()  # reste active toute la session : rappels, recherche, connecteur
        for nom, rappel in (("briefing", self.montrer_briefing), ("panneau", self.montrer_panneau)):
            action = Gio.SimpleAction.new(nom, None)
            action.connect("activate", lambda *_a, f=rappel: f())
            self.add_action(action)
        GLib.timeout_add_seconds(60, self._chaque_minute)
        self.actualiser()
        threading.Thread(target=self._boucle_etat, daemon=True).start()
        if self.connecteur.actif:
            threading.Thread(target=self._boucle_outils, daemon=True).start()

    def do_dbus_register(self, connexion, chemin):
        Adw.Application.do_dbus_register(self, connexion, chemin)
        self.recherche.enregistrer(connexion)
        return True

    def do_dbus_unregister(self, connexion, chemin):
        self.recherche.retirer(connexion)
        Adw.Application.do_dbus_unregister(self, connexion, chemin)

    def do_activate(self):
        self.montrer_panneau()

    def do_command_line(self, ligne):
        arguments = ligne.get_arguments()[1:]
        commande = arguments[0] if arguments else "service"
        if commande == "demarrage":
            if self.config.briefing_a_l_ouverture:
                self.montrer_briefing()
        elif commande == "briefing":
            self.montrer_briefing()
        elif commande == "panneau":
            self.montrer_panneau()
        elif commande == "demander":
            self._demander(arguments[1:])
        elif commande != "service":
            ligne.printerr(f"Commande inconnue : {commande}\n")
            return 2
        return 0

    # --- Fenêtres -----------------------------------------------------------

    def montrer_briefing(self):
        from .ui.briefing import FenetreBriefing
        if self.fenetre_briefing is None:
            self.fenetre_briefing = FenetreBriefing(self)
            if self.briefing:
                self.fenetre_briefing.afficher(self.briefing)
        self.fenetre_briefing.present()
        self.actualiser()
        return self.fenetre_briefing

    def montrer_panneau(self):
        from .ui.panneau import Panneau
        if self.panneau is None:
            self.panneau = Panneau(self)
        self.panneau.maj_etat()
        self.panneau.present()
        return self.panneau

    def _demander(self, arguments):
        action, fichiers, texte = "resumer", [], ""
        i = 0
        while i < len(arguments):
            if arguments[i] in ("--action", "--texte") and i + 1 < len(arguments):
                if arguments[i] == "--action":
                    action = arguments[i + 1]
                else:
                    texte = arguments[i + 1]
                i += 2
            else:
                fichiers.append(arguments[i])
                i += 1
        demande = texte or DEMANDES.get(action, "{}").format(", ".join(fichiers))
        self.montrer_panneau().demander(demande)

    # --- Briefing -----------------------------------------------------------

    def sources(self):
        return [SourceIA(self.connecteur), AgendaEvolution(), self.taches]

    def actualiser(self):
        def travail():
            briefing = construire(date.today(), self.sources())
            try:
                enregistrer_cache(briefing, self.config.dossier_donnees)
            except OSError:
                pass
            GLib.idle_add(self._briefing_pret, briefing)
        threading.Thread(target=travail, daemon=True).start()

    def _briefing_pret(self, briefing):
        self.briefing = briefing
        if self.fenetre_briefing is not None:
            self.fenetre_briefing.afficher(briefing)
        return False

    def ajouter_tache(self, titre: str):
        self.taches.ajouter(titre)
        self.actualiser()

    def basculer_tache(self, ident: str, fait: bool):
        self.taches.basculer(ident, fait)

    # --- Rappels et notifications -------------------------------------------

    def notifier(self, titre: str, texte: str, action: str = "app.panneau"):
        def envoyer():
            notification = Gio.Notification.new(titre)
            notification.set_body(texte)
            notification.set_default_action(action)
            self.send_notification(None, notification)
            return False
        GLib.idle_add(envoyer)

    def _chaque_minute(self):
        self._minutes += 1
        if self._minutes % ACTUALISATION_MINUTES == 0:
            self.actualiser()
        maintenant = datetime.now()
        for element in (self.briefing.rendez_vous if self.briefing else []):
            if not element.debut:
                continue
            avant = (element.debut - maintenant).total_seconds()
            cle = f"{element.ident or element.titre}@{element.debut.isoformat()}"
            if 0 <= avant <= self.config.rappel_minutes * 60 and cle not in self._rappels_faits:
                self._rappels_faits.add(cle)
                corps = " · ".join(p for p in (element.titre, element.detail) if p)
                self.notifier(f"Rendez-vous à {element.debut:%H:%M}", corps, "app.briefing")
        return True

    # --- État des connexions (pastilles de la barre du haut) ------------------

    def _boucle_etat(self):
        sondes = Sondes(self.config, self.connecteur)
        while True:
            try:
                publier(sondes.mesurer())
            except Exception:
                pass
            time.sleep(30)

    # --- Connecteur : outils demandés par l'IA métier ------------------------

    def _boucle_outils(self):
        try:
            self.connecteur.annoncer_outils(self.moteur.catalogue())
        except ConnecteurIndisponible:
            pass
        while True:
            if arret_actif(self.config):
                time.sleep(30)
                continue
            try:
                appel = self.connecteur.appel_outil_suivant()
            except ConnecteurIndisponible:
                time.sleep(60)
                continue
            if not appel:
                continue
            resultat, erreur = None, None
            try:
                resultat = self.moteur.executer(appel.get("outil", ""), appel.get("arguments") or {},
                                                origine="ia-metier")
            except (Refus, ArretUrgence) as exception:
                erreur = str(exception)
            except Exception as exception:
                erreur = f"Erreur sur le poste : {exception}"
            try:
                self.connecteur.envoyer_resultat(str(appel.get("id", "")), resultat, erreur)
            except ConnecteurIndisponible:
                pass

    def basculer_arret(self):
        if arret_actif(self.config):
            lever_arret(self.config)
            self.notifier(self.config.nom, "L'IA peut de nouveau agir sur ce poste.")
        else:
            activer_arret(self.config)
            self.notifier(self.config.nom, "Arrêt d'urgence : l'IA n'agit plus sur ce poste.")
