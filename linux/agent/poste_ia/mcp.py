"""Serveur MCP (Model Context Protocol) sur l'entrée/sortie standard, exposant les outils du poste."""
from __future__ import annotations

import json
import sys

from . import VERSION
from .permissions import ArretUrgence, Refus

VERSION_PROTOCOLE = "2025-06-18"


def _reponse(ident, resultat=None, erreur=None):
    message = {"jsonrpc": "2.0", "id": ident}
    if erreur is not None:
        message["error"] = erreur
    else:
        message["result"] = resultat
    return message


def traiter(moteur, message: dict) -> dict | None:
    """Traite un message JSON-RPC ; renvoie la réponse, ou None pour une notification."""
    methode = message.get("method", "")
    ident = message.get("id")
    parametres = message.get("params") or {}
    if ident is None:
        return None
    if methode == "initialize":
        return _reponse(ident, {
            "protocolVersion": parametres.get("protocolVersion", VERSION_PROTOCOLE),
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "poste-ia", "version": VERSION},
        })
    if methode == "ping":
        return _reponse(ident, {})
    if methode == "tools/list":
        outils = [{"name": o["name"], "description": o["description"], "inputSchema": o["inputSchema"]}
                  for o in moteur.catalogue()]
        return _reponse(ident, {"tools": outils})
    if methode == "tools/call":
        try:
            resultat = moteur.executer(parametres.get("name", ""), parametres.get("arguments") or {}, origine="mcp")
            texte, erreur = json.dumps(resultat, ensure_ascii=False, default=str), False
        except (Refus, ArretUrgence) as exception:
            texte, erreur = str(exception), True
        except Exception as exception:
            texte, erreur = f"Erreur sur le poste : {exception}", True
        return _reponse(ident, {"content": [{"type": "text", "text": texte}], "isError": erreur})
    return _reponse(ident, erreur={"code": -32601, "message": f"Méthode inconnue : {methode}"})


def servir(moteur, entree=None, sortie=None) -> None:
    entree = entree or sys.stdin
    sortie = sortie or sys.stdout
    for ligne in entree:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            message = json.loads(ligne)
        except ValueError:
            reponse = _reponse(None, erreur={"code": -32700, "message": "JSON invalide"})
        else:
            reponse = traiter(moteur, message)
        if reponse is not None:
            sortie.write(json.dumps(reponse, ensure_ascii=False) + "\n")
            sortie.flush()
