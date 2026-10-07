# Affichage de l'installation : logo de vague, barre de progression générale
# et défilement des étapes en cours.
from __future__ import annotations

DOCUMENTATION = r"""
name: poste_notaire
type: stdout
short_description: Affichage de l'installation du poste collaborateur notaire
description:
  - Logo, barre de progression générale fixe en haut de la fenêtre et défilement des étapes en dessous.
  - Écrit aussi un journal lisible dans le fichier indiqué par la variable d'environnement LC_JOURNAL.
"""

import os
import shutil
import sys
import threading
import time

from ansible.playbook.block import Block
from ansible.playbook.handler import Handler
from ansible.plugins.callback import CallbackBase

TITRE = "Installation poste collaborateur notaire"
SOUS_TITRE = "Ubuntu 26.04 · GNOME 50 · déploiement automatisé"
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "files", "ui", "logo.txt")
ROUE = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
ROLES = {
    "base": "Socle système",
    "purge": "Nettoyage",
    "branding": "Apparence",
    "browser": "Navigateurs",
    "tools": "Outils",
    "agent": "IA métier",
}


def _couleur(rvb, code256):
    if os.environ.get("COLORTERM", "") in ("truecolor", "24bit"):
        return "\x1b[38;2;%d;%d;%dm" % rvb
    return "\x1b[38;5;%dm" % code256


VAGUE = _couleur((168, 134, 90), 137)
SARCELLE = _couleur((33, 144, 164), 31)
VERT = "\x1b[38;5;71m"
ORANGE = "\x1b[38;5;172m"
ROUGE = "\x1b[38;5;167m"
GRAS = "\x1b[1m"
DOUX = "\x1b[2m"
RAZ = "\x1b[0m"


def compter_taches(elements):
    """Nombre de tâches d'une liste de blocs compilés (hors tâches internes « meta »)."""
    total = 0
    for element in elements:
        if isinstance(element, Block):
            total += compter_taches(element.block)
        elif element.action not in ("meta", "ansible.builtin.meta"):
            total += 1
    return total


def couper(texte, longueur):
    return texte if len(texte) <= longueur else texte[: max(longueur - 1, 0)] + "…"


class Ecran:
    """En-tête fixe (logo, barre, étape en cours) et zone de défilement en dessous."""

    def __init__(self):
        self.sortie = sys.stdout
        self.interactif = self.sortie.isatty()
        self.verrou = threading.RLock()
        self.arret = threading.Event()
        self.total = 0
        self.faites = 0
        self.etape = ""
        self.tour = 0
        self.rang = 0
        self.debut = time.monotonic()
        self.colonnes, self.lignes = shutil.get_terminal_size((100, 32))
        self.journal = self._ouvrir_journal()

    def _ouvrir_journal(self):
        chemin = os.environ.get("LC_JOURNAL")
        if not chemin:
            return None
        try:
            os.makedirs(os.path.dirname(chemin), exist_ok=True)
            return open(chemin, "a", encoding="utf-8")
        except OSError:
            return None

    def _ecrire(self, texte):
        self.sortie.write(texte)
        self.sortie.flush()

    def _centrer(self, texte, longueur_visible):
        return " " * max((self.colonnes - longueur_visible) // 2, 0) + texte

    def demarrer(self):
        if not self.interactif:
            self._ecrire(TITRE + "\n")
            return
        try:
            with open(LOGO, encoding="utf-8") as fichier:
                logo = fichier.read().rstrip("\n").split("\n")
        except OSError:
            logo = []
        tampon = ["\x1b]0;%s\x07\x1b[?25l\x1b[2J\x1b[H" % TITRE]
        lignes = 0
        if self.lignes >= len(logo) + 19:
            tampon.append("\n")
            lignes += 1
            for ligne in logo:
                tampon.append(self._centrer(VAGUE + ligne + RAZ, len(ligne)) + "\n")
                lignes += 1
        titre = TITRE.upper()
        tampon.append("\n" + self._centrer(GRAS + SARCELLE + titre + RAZ, len(titre)) + "\n")
        tampon.append(self._centrer(DOUX + SOUS_TITRE + RAZ, len(SOUS_TITRE)) + "\n\n")
        lignes += 4
        self.rang = lignes + 1
        tampon.append("\x1b[%d;1H%s%s%s" % (self.rang + 2, DOUX, "─" * self.colonnes, RAZ))
        # Zone de défilement : tout ce qui est sous la barre.
        tampon.append("\x1b[%d;%dr\x1b[%d;1H" % (self.rang + 3, self.lignes, self.rang + 3))
        self._ecrire("".join(tampon))
        self.dessiner()
        threading.Thread(target=self._animer, daemon=True).start()

    def _animer(self):
        while not self.arret.wait(0.12):
            self.tour += 1
            self.dessiner()

    def dessiner(self):
        if not self.interactif or not self.rang:
            return
        with self.verrou:
            total = max(self.total, 1)
            faites = min(self.faites, total)
            ratio = faites / total
            ecoule = int(time.monotonic() - self.debut)
            infos = " %3d %%  %d/%d  %02d:%02d" % (ratio * 100, faites, total, ecoule // 60, ecoule % 60)
            largeur = max(self.colonnes - len(infos) - 4, 10)
            plein = int(largeur * ratio)
            barre = "  %s%s%s%s%s%s%s" % (SARCELLE, "█" * plein, DOUX, "░" * (largeur - plein), RAZ, GRAS, infos) + RAZ
            if self.etape:
                roue = ROUE[self.tour % len(ROUE)]
                libelle = "  %s%s%s %s" % (SARCELLE, roue, RAZ, couper(self.etape, self.colonnes - 6))
            else:
                libelle = ""
            self._ecrire("\x1b7\x1b[%d;1H\x1b[2K%s\x1b[%d;1H\x1b[2K%s\x1b8" % (self.rang, barre, self.rang + 1, libelle))

    def ajouter_total(self, nombre):
        self.total += nombre
        self.dessiner()

    def en_cours(self, libelle):
        self.etape = libelle
        self.dessiner()

    def ligne(self, icone, couleur, texte, avancer=True):
        with self.verrou:
            if avancer:
                self.faites += 1
            if self.interactif:
                self._ecrire("  %s%s%s %s\n" % (couleur, icone, RAZ, couper(texte, self.colonnes - 6)))
            else:
                self._ecrire("%s %s\n" % (icone, texte))
            if self.journal:
                self.journal.write("%s %s %s\n" % (time.strftime("%H:%M:%S"), icone, texte))
                self.journal.flush()
        self.dessiner()

    def detail(self, texte):
        with self.verrou:
            for morceau in texte.strip().splitlines()[:6]:
                if self.interactif:
                    self._ecrire("      %s%s%s\n" % (DOUX, couper(morceau, self.colonnes - 8), RAZ))
                else:
                    self._ecrire("      %s\n" % morceau)
            if self.journal:
                self.journal.write(texte.strip() + "\n")
                self.journal.flush()

    def terminer(self, reussite, etape_echouee=""):
        self.arret.set()
        with self.verrou:
            if reussite:
                self.faites = self.total
            self.etape = ""
        self.dessiner()
        chemin = os.environ.get("LC_JOURNAL", "")
        if self.interactif:
            self._ecrire("\x1b[r\x1b[%d;1H\x1b[?25h\n" % self.lignes)
        if reussite:
            self._ecrire("%s%s✓ Installation terminée.%s\n" % (GRAS, VERT, RAZ))
            self._ecrire("  Fermez la session puis reconnectez-vous pour appliquer l'apparence.\n")
        else:
            self._ecrire("%s%s✗ L'installation s'est arrêtée%s %s\n" % (GRAS, ROUGE, RAZ, etape_echouee))
            self._ecrire("  Le script peut être relancé sans risque une fois le problème corrigé.\n")
        if chemin:
            self._ecrire("  Journal : %s\n" % chemin)
        if self.journal:
            self.journal.write("%s %s\n" % (time.strftime("%H:%M:%S"), "Terminé" if reussite else "Échec"))
            self.journal.close()


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "stdout"
    CALLBACK_NAME = "poste_notaire"

    def __init__(self):
        super().__init__()
        self.ecran = Ecran()
        self.derniere_erreur = ""

    @staticmethod
    def _libelle(task):
        nom = task.name or task.action
        if nom == "Gathering Facts":
            nom = "Analyse du poste"
        role = task._role.get_name() if task._role else ""
        if role:
            return "%s · %s" % (ROLES.get(role, role), nom)
        return nom

    @staticmethod
    def _compte(result):
        return not isinstance(result._task, Handler)

    def v2_playbook_on_start(self, playbook):
        self.ecran.demarrer()

    def v2_playbook_on_play_start(self, play):
        total = compter_taches(play.compile())
        if str(play.gather_facts).lower() not in ("false", "no"):
            total += 1
        self.ecran.ajouter_total(total)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.ecran.en_cours(self._libelle(task))

    def v2_playbook_on_handler_task_start(self, task):
        self.ecran.en_cours(self._libelle(task))

    def v2_runner_on_ok(self, result):
        if result._result.get("changed"):
            self.ecran.ligne("↻", SARCELLE, self._libelle(result._task), self._compte(result))
        else:
            self.ecran.ligne("✓", VERT, self._libelle(result._task), self._compte(result))

    def v2_runner_on_skipped(self, result):
        self.ecran.ligne("·", DOUX, self._libelle(result._task) + " (sans objet)", self._compte(result))

    def v2_runner_on_failed(self, result, ignore_errors=False):
        libelle = self._libelle(result._task)
        resultat = result._result
        message = resultat.get("msg") or resultat.get("stderr") or resultat.get("module_stderr") or ""
        if ignore_errors:
            self.ecran.ligne("!", ORANGE, libelle + " (ignoré)", self._compte(result))
        else:
            self.derniere_erreur = libelle
            self.ecran.ligne("✗", ROUGE, libelle, self._compte(result))
        if message:
            self.ecran.detail(str(message))

    def v2_runner_on_unreachable(self, result):
        self.derniere_erreur = self._libelle(result._task)
        self.ecran.ligne("✗", ROUGE, self.derniere_erreur + " (poste injoignable)", self._compte(result))

    def v2_playbook_on_stats(self, stats):
        echecs = 0
        for hote in stats.processed:
            resume = stats.summarize(hote)
            echecs += resume["failures"] + resume["unreachable"]
        etape = ("à l'étape : " + self.derniere_erreur) if self.derniere_erreur else ""
        self.ecran.terminer(echecs == 0, etape)
