"""Menu « IA métier » du clic droit dans Fichiers (Nautilus)."""
import subprocess

from gi.repository import GObject, Nautilus

ACTIONS = (
    ("resumer", "Résumer"),
    ("verifier", "Vérifier cet acte"),
    ("repondre", "Préparer la réponse au client"),
    ("sceller", "Sceller (horodatage)"),
)


class MenuIAMetier(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, fichiers):
        locaux = [f for f in fichiers if f.get_uri_scheme() == "file" and not f.is_directory()]
        if not locaux:
            return []
        racine = Nautilus.MenuItem(name="PosteIA::menu", label="IA métier")
        sous_menu = Nautilus.Menu()
        racine.set_submenu(sous_menu)
        for code, libelle in ACTIONS:
            element = Nautilus.MenuItem(name=f"PosteIA::{code}", label=libelle)
            element.connect("activate", self._lancer, code, locaux)
            sous_menu.append_item(element)
        return [racine]

    @staticmethod
    def _lancer(_element, code, fichiers):
        chemins = [f.get_location().get_path() for f in fichiers]
        subprocess.Popen(["poste-ia", "demander", "--action", code, *chemins])
