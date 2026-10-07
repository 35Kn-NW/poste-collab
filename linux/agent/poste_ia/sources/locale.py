"""Tâches personnelles du collaborateur, gérées depuis le briefing."""
from __future__ import annotations

import json
import os
import uuid
from datetime import date
from pathlib import Path

from . import Briefing, Element, classer_taches


class TachesLocales:
    nom = "Tâches personnelles"

    def __init__(self, dossier: Path):
        self.chemin = Path(dossier) / "a-faire.json"

    def _lire(self) -> list[dict]:
        try:
            return json.loads(self.chemin.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def _ecrire(self, taches: list[dict]) -> None:
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        temporaire = self.chemin.with_suffix(".tmp")
        temporaire.write_text(json.dumps(taches, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporaire, self.chemin)

    def ajouter(self, titre: str, echeance: date | None = None, priorite: str = "normale") -> dict:
        tache = {"id": uuid.uuid4().hex[:12], "titre": titre.strip(), "priorite": priorite, "fait": False,
                 "echeance": echeance.isoformat() if echeance else None}
        self._ecrire(self._lire() + [tache])
        return tache

    def basculer(self, ident: str, fait: bool) -> None:
        taches = self._lire()
        for tache in taches:
            if tache.get("id") == ident:
                tache["fait"] = fait
                tache["fait_le"] = date.today().isoformat() if fait else None
        self._ecrire(taches)

    def briefing(self, jour: date) -> Briefing:
        visibles = [t for t in self._lire()
                    if not (t.get("fait") and (t.get("fait_le") or "") < jour.isoformat())]
        return classer_taches(jour, [Element.depuis_dict({**t, "modifiable": True}, self.nom) for t in visibles])
