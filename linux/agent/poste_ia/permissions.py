"""Niveaux d'autorisation de l'IA, confirmation humaine et arrêt d'urgence."""
from __future__ import annotations

import subprocess
from enum import IntEnum
from pathlib import Path

from . import config as _config


class Niveau(IntEnum):
    LIRE = 1      # consulter, dans le périmètre de l'étude
    AGIR = 2      # action réversible sur le poste, signalée à l'utilisateur
    ENGAGER = 3   # engage l'étude : confirmation explicite à chaque fois


class Refus(Exception):
    """Action refusée : hors périmètre, non confirmée ou impossible."""


class ArretUrgence(Exception):
    """L'arrêt d'urgence est actif : l'IA n'agit plus sur le poste."""


def fichier_arret(config) -> Path:
    return config.dossier_etat / "ARRET"


def arret_actif(config) -> bool:
    return _config.ARRET_SYSTEME.exists() or fichier_arret(config).exists()


def activer_arret(config) -> None:
    fichier_arret(config).parent.mkdir(parents=True, exist_ok=True)
    fichier_arret(config).touch()


def lever_arret(config) -> None:
    fichier_arret(config).unlink(missing_ok=True)


def confirmer_zenity(question: str, titre: str = "Autorisation demandée") -> bool:
    commande = [
        "zenity", "--question", "--title", titre, "--text", question,
        "--ok-label", "Autoriser", "--cancel-label", "Refuser", "--width", "460", "--no-markup",
    ]
    try:
        return subprocess.run(commande, timeout=300, check=False).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False
