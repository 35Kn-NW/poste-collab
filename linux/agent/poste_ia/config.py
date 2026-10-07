"""Configuration de l'agent, déposée par Ansible dans /etc/poste-collab/poste-ia.json."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path

FICHIER_SYSTEME = Path("/etc/poste-collab/poste-ia.json")
# Arrêt d'urgence décidé par l'administrateur pour tout le poste.
ARRET_SYSTEME = Path("/etc/poste-collab/poste-ia.arret")


def _xdg(variable: str, defaut: str) -> Path:
    return Path(os.environ.get(variable) or Path.home() / defaut) / "poste-ia"


@dataclass
class Config:
    nom: str = "IA métier"
    connecteur_url: str = ""
    connecteur_ca: str = ""
    dossiers_autorises: list[str] = field(default_factory=lambda: ["~"])
    dossier_brouillons: str = "~/Documents/Brouillons IA"
    briefing_a_l_ouverture: bool = True
    rappel_minutes: int = 15
    sondes: dict = field(default_factory=dict)
    dossier_etat: Path = field(default_factory=lambda: _xdg("XDG_STATE_HOME", ".local/state"))
    dossier_donnees: Path = field(default_factory=lambda: _xdg("XDG_DATA_HOME", ".local/share"))

    def racines(self) -> list[Path]:
        return [Path(os.path.expanduser(d)).resolve() for d in self.dossiers_autorises]


def charger(chemin: Path = FICHIER_SYSTEME) -> Config:
    donnees = {}
    if chemin.exists():
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    connus = {f.name for f in fields(Config)} - {"dossier_etat", "dossier_donnees"}
    return Config(**{cle: valeur for cle, valeur in donnees.items() if cle in connus})
