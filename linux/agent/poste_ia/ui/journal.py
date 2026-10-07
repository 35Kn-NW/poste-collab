"""Journal des actions de l'IA, consultable par le collaborateur."""
from __future__ import annotations

from gi.repository import Adw, GLib, Gtk

DECISIONS = {"execute": "exécutée", "refuse": "refusée", "arret": "bloquée (arrêt d'urgence)",
             "invalide": "invalide", "inconnu": "outil inconnu", "erreur": "en erreur"}


class FenetreJournal(Adw.Window):
    def __init__(self, parent, journal):
        super().__init__(transient_for=parent, modal=True, title="Journal des actions de l'IA",
                         default_width=560, default_height=620)
        vue = Adw.ToolbarView()
        vue.add_top_bar(Adw.HeaderBar())
        groupe = Adw.PreferencesGroup(margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        entrees = list(reversed(journal.lire()))
        if not entrees:
            groupe.add(Adw.ActionRow(title="Aucune action pour le moment"))
        for entree in entrees:
            titre = f"{entree.get('outil', '?')} · {DECISIONS.get(entree.get('decision'), entree.get('decision', ''))}"
            details = " · ".join(str(p) for p in (entree.get("horodatage", "").replace("T", " "),
                                                  entree.get("niveau"), entree.get("origine"),
                                                  entree.get("raison")) if p)
            groupe.add(Adw.ActionRow(title=GLib.markup_escape_text(titre),
                                     subtitle=GLib.markup_escape_text(details)))
        vue.set_content(Gtk.ScrolledWindow(child=groupe, vexpand=True))
        self.set_content(vue)
