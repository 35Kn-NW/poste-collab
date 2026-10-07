"""Briefing de la journée : modèle commun et agrégation des sources (IA métier, agenda, tâches)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

RUBRIQUES = ("rendez_vous", "a_faire", "a_verifier", "echeances")
LIBELLES_RUBRIQUES = {
    "rendez_vous": "Rendez-vous",
    "a_faire": "À faire",
    "a_verifier": "Points à vérifier",
    "echeances": "Échéances",
}
HORIZON_ECHEANCES = 7


def _date(valeur):
    if not valeur:
        return None
    if isinstance(valeur, date) and not isinstance(valeur, datetime):
        return valeur
    return date.fromisoformat(str(valeur)[:10])


def _instant(valeur):
    if not valeur:
        return None
    if isinstance(valeur, datetime):
        return valeur
    instant = datetime.fromisoformat(str(valeur))
    # Les heures reçues avec un fuseau sont ramenées à l'heure locale du poste.
    return instant.astimezone().replace(tzinfo=None) if instant.tzinfo else instant


@dataclass
class Element:
    titre: str
    detail: str = ""
    debut: datetime | None = None
    fin: datetime | None = None
    echeance: date | None = None
    priorite: str = "normale"
    source: str = ""
    lien: str = ""
    ident: str = ""
    fait: bool = False
    modifiable: bool = False

    @classmethod
    def depuis_dict(cls, donnees: dict, source: str = "") -> "Element":
        return cls(
            titre=str(donnees.get("titre") or "").strip() or "(sans titre)",
            detail=str(donnees.get("detail") or ""),
            debut=_instant(donnees.get("debut")),
            fin=_instant(donnees.get("fin")),
            echeance=_date(donnees.get("echeance")),
            priorite="haute" if donnees.get("priorite") == "haute" else "normale",
            source=str(donnees.get("source") or source),
            lien=str(donnees.get("lien") or ""),
            ident=str(donnees.get("id") or donnees.get("ident") or ""),
            fait=bool(donnees.get("fait", False)),
            modifiable=bool(donnees.get("modifiable", False)),
        )

    def vers_dict(self) -> dict:
        donnees = asdict(self)
        for cle in ("debut", "fin", "echeance"):
            if donnees[cle] is not None:
                donnees[cle] = donnees[cle].isoformat()
        return donnees


@dataclass
class Briefing:
    jour: date
    rendez_vous: list[Element] = field(default_factory=list)
    a_faire: list[Element] = field(default_factory=list)
    a_verifier: list[Element] = field(default_factory=list)
    echeances: list[Element] = field(default_factory=list)
    synthese: str = ""
    indicateurs: dict = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    indisponibles: dict[str, str] = field(default_factory=dict)

    def fusionner(self, autre: "Briefing") -> None:
        for rubrique in RUBRIQUES:
            getattr(self, rubrique).extend(getattr(autre, rubrique))
        if autre.synthese:
            self.synthese = f"{self.synthese}\n\n{autre.synthese}".strip()
        self.indicateurs.update(autre.indicateurs)
        self.sources.extend(autre.sources)
        self.indisponibles.update(autre.indisponibles)

    def trier(self) -> None:
        self.rendez_vous.sort(key=lambda e: e.debut or datetime.max)
        self.a_faire.sort(key=lambda e: (e.fait, e.priorite != "haute", e.echeance or date.max, e.titre.lower()))
        self.a_verifier.sort(key=lambda e: (e.priorite != "haute", e.echeance or date.max, e.titre.lower()))
        self.echeances.sort(key=lambda e: (e.echeance or date.max, e.titre.lower()))

    def tous(self) -> list[tuple[str, Element]]:
        return [(rubrique, element) for rubrique in RUBRIQUES for element in getattr(self, rubrique)]

    def vue_globale(self) -> list[tuple[str, str]]:
        restantes = sum(1 for e in self.a_faire if not e.fait)
        limite = self.jour + timedelta(days=HORIZON_ECHEANCES)
        proches = sum(1 for e in self.echeances if e.echeance and e.echeance <= limite)
        vue = [
            ("Rendez-vous", str(len(self.rendez_vous))),
            ("À faire", str(restantes)),
            ("À vérifier", str(len(self.a_verifier))),
            (f"Échéances {HORIZON_ECHEANCES} j", str(proches)),
        ]
        return vue + [(str(cle), str(valeur)) for cle, valeur in self.indicateurs.items()]

    def resume(self) -> str:
        if self.synthese:
            return self.synthese
        parties = []
        if not self.rendez_vous:
            parties.append("Aucun rendez-vous aujourd'hui.")
        else:
            premier = self.rendez_vous[0].debut
            parties.append(f"{len(self.rendez_vous)} rendez-vous aujourd'hui"
                           + (f", le premier à {premier:%H:%M}." if premier else "."))
        urgentes = [e for e in self.a_faire
                    if not e.fait and (e.priorite == "haute" or (e.echeance and e.echeance <= self.jour))]
        if urgentes:
            parties.append(f"{len(urgentes)} tâche(s) prioritaire(s) ou en retard.")
        if self.a_verifier:
            parties.append(f"{len(self.a_verifier)} point(s) à vérifier.")
        proches = [e for e in self.echeances if e.echeance and e.echeance <= self.jour + timedelta(days=2)]
        if proches:
            parties.append(f"{len(proches)} échéance(s) dans les 48 heures.")
        return " ".join(parties)

    def vers_dict(self) -> dict:
        donnees = {rubrique: [e.vers_dict() for e in getattr(self, rubrique)] for rubrique in RUBRIQUES}
        donnees.update(jour=self.jour.isoformat(), synthese=self.synthese, indicateurs=self.indicateurs,
                       sources=self.sources, indisponibles=self.indisponibles)
        return donnees

    @classmethod
    def depuis_dict(cls, donnees: dict) -> "Briefing":
        briefing = cls(jour=_date(donnees["jour"]), synthese=donnees.get("synthese", ""),
                       indicateurs=donnees.get("indicateurs", {}), sources=donnees.get("sources", []),
                       indisponibles=donnees.get("indisponibles", {}))
        for rubrique in RUBRIQUES:
            setattr(briefing, rubrique, [Element.depuis_dict(e) for e in donnees.get(rubrique, [])])
        return briefing


def classer_taches(jour: date, taches: list[Element]) -> Briefing:
    """Répartit des tâches : à faire (sans date, du jour ou en retard) ou échéances proches."""
    briefing = Briefing(jour=jour)
    limite = jour + timedelta(days=HORIZON_ECHEANCES)
    for tache in taches:
        if tache.echeance is None or tache.echeance <= jour:
            if tache.echeance and tache.echeance < jour and not tache.fait:
                tache.priorite = "haute"
            briefing.a_faire.append(tache)
        elif tache.echeance <= limite and not tache.fait:
            briefing.echeances.append(tache)
    return briefing


def construire(jour: date, sources) -> Briefing:
    """Interroge chaque source ; une source en panne n'empêche jamais le briefing."""
    briefing = Briefing(jour=jour)
    for source in sources:
        try:
            partiel = source.briefing(jour)
        except Exception as erreur:
            briefing.indisponibles[source.nom] = str(erreur) or erreur.__class__.__name__
            continue
        briefing.fusionner(partiel)
        briefing.sources.append(source.nom)
    briefing.trier()
    return briefing


def enregistrer_cache(briefing: Briefing, dossier: Path) -> None:
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    temporaire = dossier / "briefing.json.tmp"
    temporaire.write_text(json.dumps(briefing.vers_dict(), ensure_ascii=False), encoding="utf-8")
    os.replace(temporaire, dossier / "briefing.json")


def lire_cache(dossier: Path, jour: date) -> Briefing | None:
    chemin = Path(dossier) / "briefing.json"
    try:
        briefing = Briefing.depuis_dict(json.loads(chemin.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError):
        return None
    return briefing if briefing.jour == jour else None
