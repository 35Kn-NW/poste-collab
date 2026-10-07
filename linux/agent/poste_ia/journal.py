"""Journal des actions de l'IA sur le poste : une ligne JSON par action, consultable à tout moment."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class Journal:
    def __init__(self, dossier: Path):
        self.chemin = Path(dossier) / "journal.jsonl"

    def ecrire(self, **entree) -> None:
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        entree = {"horodatage": datetime.now().isoformat(timespec="seconds"), **entree}
        with self.chemin.open("a", encoding="utf-8") as fichier:
            fichier.write(json.dumps(entree, ensure_ascii=False, default=str) + "\n")

    def lire(self, nombre: int = 200) -> list[dict]:
        if not self.chemin.exists():
            return []
        entrees = []
        for ligne in self.chemin.read_text(encoding="utf-8").splitlines()[-nombre:]:
            try:
                entrees.append(json.loads(ligne))
            except ValueError:
                continue
        return entrees
