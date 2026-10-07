"""Outils que l'IA métier peut utiliser sur le poste, chacun avec son niveau d'autorisation."""
from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .journal import Journal
from .permissions import ArretUrgence, Niveau, Refus, arret_actif, confirmer_zenity

TAILLE_LECTURE_MAX = 200_000
RESULTATS_MAX = 200
SCHEMES_AUTORISES = ("http://", "https://", "mailto:")


@dataclass
class Outil:
    nom: str
    description: str
    niveau: Niveau
    parametres: dict
    fonction: Callable[..., Any]
    signaler: bool = True

    def schema(self) -> dict:
        return {"type": "object", "additionalProperties": False, **self.parametres}


def _abreger(valeur, longueur=200):
    if isinstance(valeur, str) and len(valeur) > longueur:
        return valeur[:longueur] + "…"
    if isinstance(valeur, dict):
        return {cle: _abreger(v, longueur) for cle, v in valeur.items()}
    return valeur


def _presenter(arguments: dict) -> str:
    return "\n".join(f"{cle} : {_abreger(str(valeur), 300)}" for cle, valeur in arguments.items())


class Moteur:
    """Exécute les demandes de l'IA en appliquant périmètre, niveau, confirmation et journal."""

    def __init__(self, config, journal: Journal | None = None, confirmer=confirmer_zenity,
                 notifier=None, connecteur=None):
        self.config = config
        self.journal = journal or Journal(config.dossier_etat)
        self.confirmer = confirmer
        self.notifier = notifier
        self.connecteur = connecteur
        self.outils = {outil.nom: outil for outil in OUTILS}

    def lister(self) -> list[Outil]:
        return list(self.outils.values())

    def catalogue(self) -> list[dict]:
        return [
            {"name": o.nom, "description": o.description, "niveau": o.niveau.name.lower(),
             "inputSchema": o.schema()}
            for o in self.lister()
        ]

    def executer(self, nom: str, arguments: dict | None = None, origine: str = "ia"):
        arguments = arguments or {}
        trace = {"outil": nom, "origine": origine, "arguments": _abreger(arguments)}
        outil = self.outils.get(nom)
        if outil is None:
            self.journal.ecrire(**trace, decision="inconnu")
            raise Refus(f"Outil inconnu : {nom}")
        trace["niveau"] = outil.niveau.name.lower()

        if arret_actif(self.config):
            self.journal.ecrire(**trace, decision="arret")
            raise ArretUrgence("Arrêt d'urgence actif : aucune action de l'IA n'est exécutée.")

        attendus = outil.parametres.get("properties", {})
        inconnus = sorted(set(arguments) - set(attendus))
        manquants = [p for p in outil.parametres.get("required", []) if p not in arguments]
        if inconnus or manquants:
            self.journal.ecrire(**trace, decision="invalide")
            raise Refus(f"Paramètres invalides pour {nom} (inconnus : {inconnus}, manquants : {manquants}).")

        if outil.niveau >= Niveau.ENGAGER:
            question = f"{self.config.nom} demande l'autorisation de : {outil.description}\n\n{_presenter(arguments)}"
            if not self.confirmer(question):
                self.journal.ecrire(**trace, decision="refuse")
                raise Refus("Action refusée par l'utilisateur.")

        try:
            resultat = outil.fonction(self, **arguments)
        except Refus as erreur:
            self.journal.ecrire(**trace, decision="refuse", raison=str(erreur))
            raise
        except Exception as erreur:
            self.journal.ecrire(**trace, decision="erreur", raison=str(erreur))
            raise
        self.journal.ecrire(**trace, decision="execute")
        if outil.niveau == Niveau.AGIR and outil.signaler:
            self.signaler(f"{self.config.nom} : {outil.description}", _presenter(arguments))
        return resultat

    def signaler(self, titre: str, texte: str) -> None:
        if self.notifier:
            self.notifier(titre, texte)
            return
        try:
            subprocess.run(["notify-send", "-a", self.config.nom, titre, texte], timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def dans_perimetre(self, chemin: str) -> Path:
        """Chemin réel (liens résolus) s'il est dans le périmètre et ne passe par aucun élément caché."""
        cible = Path(os.path.expanduser(str(chemin))).resolve()
        for racine in self.config.racines():
            if cible == racine or racine in cible.parents:
                if any(partie.startswith(".") for partie in cible.relative_to(racine).parts):
                    raise Refus(f"Élément caché, réservé au système : {chemin}")
                return cible
        raise Refus(f"Hors du périmètre de l'étude : {chemin}")


# --- Outils -------------------------------------------------------------------

def _texte(description: str) -> dict:
    return {"type": "string", "description": description}


def _lancer(uri: str) -> None:
    subprocess.Popen(["xdg-open", uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _fichiers_lister(moteur: Moteur, dossier: str):
    chemin = moteur.dans_perimetre(dossier)
    if not chemin.is_dir():
        raise Refus(f"Dossier introuvable : {dossier}")
    elements = []
    for entree in sorted(chemin.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
        if entree.name.startswith("."):
            continue
        infos = entree.stat()
        elements.append({
            "nom": entree.name,
            "chemin": str(entree),
            "type": "dossier" if entree.is_dir() else "fichier",
            "taille": infos.st_size,
            "modifie": datetime.fromtimestamp(infos.st_mtime).isoformat(timespec="minutes"),
        })
        if len(elements) >= RESULTATS_MAX:
            break
    return {"dossier": str(chemin), "elements": elements}


def _fichiers_chercher(moteur: Moteur, motif: str):
    motif_bas = motif.lower()
    trouves = []
    for racine in moteur.config.racines():
        for dossier, sous_dossiers, fichiers in os.walk(racine):
            sous_dossiers[:] = [s for s in sous_dossiers if not s.startswith(".")]
            for nom in fichiers:
                nom_bas = nom.lower()
                if nom.startswith(".") or not (motif_bas in nom_bas or fnmatch.fnmatch(nom_bas, motif_bas)):
                    continue
                trouves.append(os.path.join(dossier, nom))
                if len(trouves) >= RESULTATS_MAX:
                    return {"motif": motif, "resultats": trouves, "tronque": True}
    return {"motif": motif, "resultats": trouves, "tronque": False}


def _fichier_lire(moteur: Moteur, chemin: str):
    fichier = moteur.dans_perimetre(chemin)
    if not fichier.is_file():
        raise Refus(f"Fichier introuvable : {chemin}")
    if fichier.suffix.lower() == ".pdf":
        if not shutil.which("pdftotext"):
            raise Refus("Lecture des PDF indisponible sur ce poste (pdftotext absent).")
        texte = subprocess.run(["pdftotext", "-layout", str(fichier), "-"], capture_output=True,
                               text=True, timeout=60, check=True).stdout
    else:
        with fichier.open("rb") as flux:
            texte = flux.read(TAILLE_LECTURE_MAX + 1).decode("utf-8", errors="replace")
    return {"chemin": str(fichier), "texte": texte[:TAILLE_LECTURE_MAX], "tronque": len(texte) > TAILLE_LECTURE_MAX}


def _notifier(moteur: Moteur, titre: str, texte: str):
    moteur.signaler(titre, texte)
    return {"affiche": True}


def _ouvrir(moteur: Moteur, cible: str):
    uri = cible if cible.startswith(SCHEMES_AUTORISES) else moteur.dans_perimetre(cible).as_uri()
    _lancer(uri)
    return {"ouvert": uri}


def _brouillon_ecrire(moteur: Moteur, nom: str, contenu: str):
    dossier = moteur.dans_perimetre(moteur.config.dossier_brouillons)
    dossier.mkdir(parents=True, exist_ok=True)
    base = re.sub(r"[^\w .,()'-]", "_", nom).strip(" .") or "brouillon"
    if not Path(base).suffix:
        base += ".txt"
    cible, numero = dossier / base, 2
    while cible.exists():
        cible = dossier / f"{Path(base).stem} ({numero}){Path(base).suffix}"
        numero += 1
    cible.write_text(contenu, encoding="utf-8")
    return {"chemin": str(cible)}


def _courriel_preparer(moteur: Moteur, destinataires: str, objet: str, corps: str):
    adresses = ",".join(urllib.parse.quote(a.strip(), safe="@.+-_") for a in destinataires.split(",") if a.strip())
    uri = f"mailto:{adresses}?subject={urllib.parse.quote(objet)}&body={urllib.parse.quote(corps)}"
    _lancer(uri)
    return {"prepare": True, "envoye": False,
            "message": "Le courriel est ouvert dans la messagerie : le collaborateur le relit et l'envoie lui-même."}


def _document_sceller(moteur: Moteur, chemin: str):
    fichier = moteur.dans_perimetre(chemin)
    if not fichier.is_file():
        raise Refus(f"Fichier introuvable : {chemin}")
    if moteur.connecteur is None or not moteur.connecteur.actif:
        raise Refus("Connecteur IA métier non configuré : scellement impossible.")
    empreinte = hashlib.sha256()
    with fichier.open("rb") as flux:
        for bloc in iter(lambda: flux.read(1 << 20), b""):
            empreinte.update(bloc)
    return moteur.connecteur.sceller(empreinte.hexdigest(), fichier.name)


OUTILS = [
    Outil("fichiers_lister", "lister le contenu d'un dossier", Niveau.LIRE,
          {"properties": {"dossier": _texte("Chemin du dossier")}, "required": ["dossier"]}, _fichiers_lister),
    Outil("fichiers_chercher", "chercher des fichiers par nom", Niveau.LIRE,
          {"properties": {"motif": _texte("Partie du nom ou motif (*.pdf)")}, "required": ["motif"]}, _fichiers_chercher),
    Outil("fichier_lire", "lire le texte d'un document (texte ou PDF)", Niveau.LIRE,
          {"properties": {"chemin": _texte("Chemin du fichier")}, "required": ["chemin"]}, _fichier_lire),
    Outil("notifier", "afficher une notification", Niveau.AGIR,
          {"properties": {"titre": _texte("Titre"), "texte": _texte("Message")}, "required": ["titre", "texte"]},
          _notifier, signaler=False),
    Outil("ouvrir", "ouvrir un document ou une adresse web", Niveau.AGIR,
          {"properties": {"cible": _texte("Chemin du fichier, ou adresse http(s) / mailto")}, "required": ["cible"]},
          _ouvrir),
    Outil("brouillon_ecrire", "créer un brouillon dans « Brouillons IA »", Niveau.AGIR,
          {"properties": {"nom": _texte("Nom du fichier"), "contenu": _texte("Texte du brouillon")},
           "required": ["nom", "contenu"]}, _brouillon_ecrire),
    Outil("courriel_preparer", "préparer un courriel (le collaborateur l'envoie lui-même)", Niveau.AGIR,
          {"properties": {"destinataires": _texte("Adresses séparées par des virgules"), "objet": _texte("Objet"),
                          "corps": _texte("Texte du message")}, "required": ["destinataires", "objet", "corps"]},
          _courriel_preparer),
    Outil("document_sceller", "sceller ce document dans le registre d'horodatage", Niveau.ENGAGER,
          {"properties": {"chemin": _texte("Chemin du document")}, "required": ["chemin"]}, _document_sceller),
]
