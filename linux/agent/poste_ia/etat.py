"""État des connexions affiché en haut de l'écran : REAL, IA métier, Office 365, VPN, base de l'étude."""
from __future__ import annotations

import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from .sources.connecteur import ConnecteurIndisponible

OK, DEGRADE, ERREUR, INACTIF = "ok", "degrade", "erreur", "inactif"
SERVICES = (
    ("real", "REAL"),
    ("ia", "IA métier"),
    ("m365", "Office 365"),
    ("vpn", "VPN"),
    ("base", "Base étude"),
)
URL_M365 = "https://outlook.office365.com"
RESEAU = Path("/sys/class/net")
PREFIXES_VPN = ("wg", "tun", "tap", "vpn", "ppp", "ipsec", "nordlynx")


@dataclass
class Etat:
    niveau: str
    detail: str


def joignable_tcp(hote: str, port: int, delai: float = 3.0) -> bool:
    try:
        with socket.create_connection((hote, int(port)), timeout=delai):
            return True
    except (OSError, ValueError):
        return False


def joignable_https(url: str, delai: float = 5.0) -> bool:
    requete = urllib.request.Request(url, method="HEAD")
    try:
        urllib.request.urlopen(requete, timeout=delai, context=ssl.create_default_context())
        return True
    except urllib.error.HTTPError:
        return True  # le serveur a répondu, même par une erreur : il est joignable
    except (urllib.error.URLError, OSError, ValueError):
        return False


def interfaces_vpn(racine: Path = RESEAU) -> list[str]:
    """Interfaces VPN actives (WireGuard, OpenVPN, IPsec…)."""
    try:
        noms = sorted(os.listdir(racine))
    except OSError:
        return []
    actives = []
    for nom in noms:
        dossier = Path(racine) / nom

        def lire(fichier):
            try:
                return (dossier / fichier).read_text(encoding="utf-8", errors="ignore").strip()
            except OSError:
                return ""

        if lire("operstate") == "down":
            continue
        if nom.startswith(PREFIXES_VPN) or "DEVTYPE=wireguard" in lire("uevent"):
            actives.append(nom)
    return actives


def compte_m365_relie(dossier_sources: Path) -> bool:
    try:
        return any("microsoft365" in f.read_text(encoding="utf-8", errors="ignore")
                   for f in Path(dossier_sources).glob("*.source"))
    except OSError:
        return False


def _sources_evolution() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "evolution" / "sources"


class Sondes:
    def __init__(self, config, connecteur, racine_reseau: Path = RESEAU, sources_evolution: Path | None = None,
                 https=joignable_https, tcp=joignable_tcp):
        self.config = config
        self.connecteur = connecteur
        self.racine_reseau = racine_reseau
        self.sources_evolution = sources_evolution or _sources_evolution()
        self.https = https
        self.tcp = tcp

    def _hote(self, nom: str, port_defaut: int):
        reglage = self.config.sondes.get(nom) or {}
        return reglage.get("hote") or "", reglage.get("port") or port_defaut

    def real(self) -> Etat:
        hote, port = self._hote("real", 443)
        if not hote:
            return Etat(INACTIF, "sonde non configurée")
        return Etat(OK, "réseau joignable") if self.tcp(hote, port) else Etat(ERREUR, "réseau injoignable")

    def ia(self) -> Etat:
        if not self.connecteur.actif:
            return Etat(INACTIF, "non connectée à ce poste")
        try:
            self.connecteur.etat()
        except ConnecteurIndisponible as erreur:
            return Etat(ERREUR, str(erreur))
        return Etat(OK, "connectée")

    def m365(self) -> Etat:
        if not self.https(URL_M365):
            return Etat(ERREUR, "Microsoft 365 injoignable")
        if not compte_m365_relie(self.sources_evolution):
            return Etat(DEGRADE, "joignable, messagerie non reliée sur ce poste")
        return Etat(OK, "connecté")

    def vpn(self) -> Etat:
        actives = interfaces_vpn(self.racine_reseau)
        if actives:
            return Etat(OK, f"connecté ({', '.join(actives)})")
        hote, port = self._hote("bureau", 443)
        if not hote:
            return Etat(INACTIF, "aucun VPN actif")
        if self.tcp(hote, port):
            return Etat(INACTIF, "au bureau : VPN inutile")
        return Etat(DEGRADE, "hors du bureau : VPN non connecté")

    def base(self) -> Etat:
        hote, port = self._hote("base", 5432)
        if not hote:
            return Etat(INACTIF, "sonde non configurée")
        return Etat(OK, "base joignable") if self.tcp(hote, port) else Etat(ERREUR, "base injoignable")

    def mesurer(self) -> dict:
        with ThreadPoolExecutor(max_workers=len(SERVICES)) as groupe:
            futurs = {cle: groupe.submit(getattr(self, cle)) for cle, _ in SERVICES}
            resultats = {}
            for cle, futur in futurs.items():
                try:
                    resultats[cle] = futur.result(timeout=20)
                except Exception as erreur:
                    resultats[cle] = Etat(ERREUR, f"sonde en échec ({erreur})")
        return {"horodatage": int(time.time()),
                "services": {cle: {"libelle": libelle, **asdict(resultats[cle])} for cle, libelle in SERVICES}}


def fichier_etat() -> Path:
    base = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(base) / "poste-collab" / "etat.json"


def publier(etat: dict, chemin: Path | None = None) -> Path:
    chemin = Path(chemin or fichier_etat())
    chemin.parent.mkdir(parents=True, exist_ok=True)
    temporaire = chemin.with_suffix(".tmp")
    temporaire.write_text(json.dumps(etat, ensure_ascii=False), encoding="utf-8")
    os.replace(temporaire, chemin)
    return chemin
