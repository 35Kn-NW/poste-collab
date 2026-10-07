"""Jeton du connecteur, rangé dans le trousseau GNOME (jamais dans un fichier en clair)."""
from __future__ import annotations

from . import APP_ID

ATTRIBUTS = {"usage": "connecteur"}


def _secret():
    try:
        import gi
        gi.require_version("Secret", "1")
        from gi.repository import Secret
    except (ImportError, ValueError):
        return None
    return Secret


def _schema(secret):
    return secret.Schema.new(APP_ID, secret.SchemaFlags.NONE, {"usage": secret.SchemaAttributeType.STRING})


def lire_jeton() -> str | None:
    secret = _secret()
    if secret is None:
        return None
    try:
        return secret.password_lookup_sync(_schema(secret), ATTRIBUTS, None)
    except Exception:
        return None


def enregistrer_jeton(jeton: str) -> None:
    secret = _secret()
    if secret is None:
        raise RuntimeError("Trousseau indisponible (gir1.2-secret-1 absent).")
    secret.password_store_sync(_schema(secret), ATTRIBUTS, secret.COLLECTION_DEFAULT,
                               "Jeton du connecteur IA métier", jeton, None)
