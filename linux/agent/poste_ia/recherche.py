"""Fournisseur de recherche GNOME : briefing et « Demander à l'IA métier » dans la vue d'ensemble."""
from __future__ import annotations

from gi.repository import Gio, GLib

from . import APP_ID
from .sources import LIBELLES_RUBRIQUES

CHEMIN = "/io/github/postecollab/PosteIA/SearchProvider"
INTERFACE = """<node><interface name="org.gnome.Shell.SearchProvider2">
<method name="GetInitialResultSet"><arg type="as" name="terms" direction="in"/><arg type="as" name="results" direction="out"/></method>
<method name="GetSubsearchResultSet"><arg type="as" name="previous_results" direction="in"/><arg type="as" name="terms" direction="in"/><arg type="as" name="results" direction="out"/></method>
<method name="GetResultMetas"><arg type="as" name="identifiers" direction="in"/><arg type="aa{sv}" name="metas" direction="out"/></method>
<method name="ActivateResult"><arg type="s" name="identifier" direction="in"/><arg type="as" name="terms" direction="in"/><arg type="u" name="timestamp" direction="in"/></method>
<method name="LaunchSearch"><arg type="as" name="terms" direction="in"/><arg type="u" name="timestamp" direction="in"/></method>
</interface></node>"""


class FournisseurRecherche:
    def __init__(self, application):
        self.application = application
        self._enregistrements = {}

    def enregistrer(self, connexion) -> None:
        interface = Gio.DBusNodeInfo.new_for_xml(INTERFACE).interfaces[0]
        self._enregistrements[connexion] = connexion.register_object(CHEMIN, interface, self._appel, None, None)

    def retirer(self, connexion) -> None:
        ident = self._enregistrements.pop(connexion, None)
        if ident:
            connexion.unregister_object(ident)

    def _elements(self):
        briefing = self.application.briefing
        return briefing.tous() if briefing else []

    def _resultats(self, termes):
        termes = [t for t in termes if t.strip()]
        if not termes:
            return []
        minuscules = [t.lower() for t in termes]
        trouves = [f"element:{i}" for i, (_r, e) in enumerate(self._elements())
                   if all(t in f"{e.titre} {e.detail}".lower() for t in minuscules)]
        return trouves[:6] + ["ia:" + " ".join(termes)]

    def _meta(self, ident: str):
        if ident.startswith("ia:"):
            nom, description, icone = f"Demander à {self.application.config.nom}", ident[3:], APP_ID
        else:
            elements = self._elements()
            index = int(ident.split(":", 1)[1])
            if index >= len(elements):
                return None
            rubrique, element = elements[index]
            nom = element.titre
            description = " · ".join(p for p in (LIBELLES_RUBRIQUES[rubrique], element.detail) if p)
            icone = "x-office-calendar"
        return {"id": GLib.Variant("s", ident), "name": GLib.Variant("s", nom),
                "description": GLib.Variant("s", description),
                "gicon": GLib.Variant("s", Gio.ThemedIcon.new(icone).to_string())}

    def _activer(self, ident: str, termes):
        if ident.startswith("ia:"):
            self.application.montrer_panneau().demander(ident[3:])
        else:
            self.application.montrer_briefing()
        return False

    def _appel(self, _connexion, _emetteur, _chemin, _interface, methode, parametres, invocation):
        arguments = parametres.unpack()
        if methode == "GetInitialResultSet":
            invocation.return_value(GLib.Variant("(as)", (self._resultats(arguments[0]),)))
        elif methode == "GetSubsearchResultSet":
            invocation.return_value(GLib.Variant("(as)", (self._resultats(arguments[1]),)))
        elif methode == "GetResultMetas":
            metas = [m for m in (self._meta(i) for i in arguments[0]) if m]
            invocation.return_value(GLib.Variant("(aa{sv})", (metas,)))
        elif methode == "ActivateResult":
            GLib.idle_add(self._activer, arguments[0], arguments[1])
            invocation.return_value(None)
        elif methode == "LaunchSearch":
            GLib.idle_add(self._activer, "ia:" + " ".join(arguments[0]), arguments[0])
            invocation.return_value(None)
