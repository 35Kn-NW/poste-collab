"""Connecteur vers l'IA métier distante (contrat : docs/IA-POSTE.md)."""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from datetime import date

from .. import VERSION

PREFIXE = "/poste/v1"


class ConnecteurIndisponible(Exception):
    """Le serveur de l'IA métier n'est pas configuré ou ne répond pas."""


class Connecteur:
    def __init__(self, config, jeton: str | None = None):
        self.config = config
        self._jeton = jeton

    @property
    def actif(self) -> bool:
        return bool(self.config.connecteur_url)

    def _jeton_courant(self) -> str:
        if self._jeton is None:
            from ..secret import lire_jeton
            self._jeton = lire_jeton() or ""
        return self._jeton

    def _ouvrir(self, methode: str, chemin: str, corps=None, accepter="application/json", delai=20):
        if not self.actif:
            raise ConnecteurIndisponible("non connectée à ce poste")
        donnees = None if corps is None else json.dumps(corps, ensure_ascii=False).encode("utf-8")
        requete = urllib.request.Request(self.config.connecteur_url.rstrip("/") + PREFIXE + chemin,
                                         data=donnees, method=methode)
        requete.add_header("Accept", accepter)
        requete.add_header("User-Agent", f"poste-ia/{VERSION}")
        if donnees is not None:
            requete.add_header("Content-Type", "application/json")
        jeton = self._jeton_courant()
        if jeton:
            requete.add_header("Authorization", f"Bearer {jeton}")
        # L'autorité du serveur de l'étude est reconnue pour cette seule connexion,
        # sans jamais être ajoutée aux autorités racines du poste.
        contexte = ssl.create_default_context(cafile=self.config.connecteur_ca or None)
        try:
            return urllib.request.urlopen(requete, timeout=delai, context=contexte)
        except urllib.error.HTTPError as erreur:
            raise ConnecteurIndisponible(f"réponse {erreur.code} du serveur") from erreur
        except (urllib.error.URLError, OSError) as erreur:
            raise ConnecteurIndisponible(f"serveur injoignable ({getattr(erreur, 'reason', erreur)})") from erreur

    def _json(self, methode: str, chemin: str, corps=None, delai=20):
        with self._ouvrir(methode, chemin, corps, delai=delai) as reponse:
            if reponse.status == 204:
                return None
            contenu = reponse.read().decode("utf-8")
        try:
            return json.loads(contenu) if contenu else None
        except ValueError as erreur:
            raise ConnecteurIndisponible("réponse illisible du serveur") from erreur

    def briefing(self, jour: date) -> dict:
        return self._json("GET", f"/briefing?date={jour.isoformat()}") or {}

    def converser(self, messages: list[dict]):
        """Envoie la conversation ; renvoie les morceaux de réponse au fil de l'eau (SSE)."""
        with self._ouvrir("POST", "/conversation", {"messages": messages}, "text/event-stream", 120) as reponse:
            for brut in reponse:
                ligne = brut.decode("utf-8").rstrip("\r\n")
                if not ligne.startswith("data:"):
                    continue
                charge = ligne[5:].strip()
                if charge == "[DONE]":
                    return
                try:
                    evenement = json.loads(charge)
                except ValueError:
                    continue
                if evenement.get("erreur"):
                    raise ConnecteurIndisponible(str(evenement["erreur"]))
                if evenement.get("delta"):
                    yield evenement["delta"]

    def annoncer_outils(self, catalogue: list[dict]) -> None:
        self._json("POST", "/outils/catalogue", {"outils": catalogue})

    def appel_outil_suivant(self, attente: int = 25):
        return self._json("GET", f"/outils/attente?delai={attente}", delai=attente + 10)

    def envoyer_resultat(self, ident: str, resultat=None, erreur: str | None = None) -> None:
        self._json("POST", "/outils/resultat", {"id": ident, "resultat": resultat, "erreur": erreur})

    def sceller(self, empreinte: str, nom: str) -> dict:
        return self._json("POST", "/sceller", {"empreinte_sha256": empreinte, "nom": nom}) or {}
