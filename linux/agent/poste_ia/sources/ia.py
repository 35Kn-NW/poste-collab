"""Source « IA métier » : briefing préparé par l'IA de l'étude (vision globale des dossiers)."""
from __future__ import annotations

from datetime import date

from . import RUBRIQUES, Briefing, Element


class SourceIA:
    nom = "IA métier"

    def __init__(self, connecteur):
        self.connecteur = connecteur

    def briefing(self, jour: date) -> Briefing:
        donnees = self.connecteur.briefing(jour)
        briefing = Briefing(jour=jour, synthese=str(donnees.get("synthese") or ""),
                            indicateurs={str(k): v for k, v in (donnees.get("indicateurs") or {}).items()})
        for rubrique in RUBRIQUES:
            setattr(briefing, rubrique, [Element.depuis_dict(e, self.nom) for e in donnees.get(rubrique) or []])
        return briefing
