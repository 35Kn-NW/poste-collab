"""Point d'entrée « poste-ia »."""
from __future__ import annotations

import sys
from datetime import date

from .config import charger

AIDE = """Usage : poste-ia <commande>

Bureau (application GNOME, une seule instance par session) :
  demarrage            briefing à l'ouverture de session (si activé)
  briefing             fenêtre « Votre journée »
  panneau              panneau de l'IA métier (Super+Espace)
  demander --action <resumer|verifier|repondre|sceller> <fichiers…>
  demander --texte "<question>"

Administration :
  briefing-texte       briefing du jour en texte
  outils               outils disponibles pour l'IA et leur niveau
  journal              actions récentes de l'IA
  arret | reprise      arrêt d'urgence de l'IA sur ce poste, ou reprise
  jeton                enregistre dans le trousseau le jeton du connecteur (lu sur l'entrée standard)
  mcp                  serveur MCP sur l'entrée/sortie standard
  version
"""


def _moteur(config):
    from .outils import Moteur
    from .sources.connecteur import Connecteur
    return Moteur(config, connecteur=Connecteur(config))


def _briefing_texte(config):
    from .sources import LIBELLES_RUBRIQUES, RUBRIQUES, construire
    from .sources.connecteur import Connecteur
    from .sources.evolution import AgendaEvolution
    from .sources.ia import SourceIA
    from .sources.locale import TachesLocales
    briefing = construire(date.today(), [SourceIA(Connecteur(config)), AgendaEvolution(),
                                         TachesLocales(config.dossier_donnees)])
    print(briefing.resume())
    print("Vue d'ensemble : " + " · ".join(f"{nom} {valeur}" for nom, valeur in briefing.vue_globale()))
    for rubrique in RUBRIQUES:
        elements = getattr(briefing, rubrique)
        print(f"\n{LIBELLES_RUBRIQUES[rubrique]} ({len(elements)})")
        for element in elements:
            quand = f"{element.debut:%H:%M} " if element.debut else (f"{element.echeance} " if element.echeance else "")
            print(f"  - {quand}{element.titre}" + (f" · {element.detail}" if element.detail else ""))
    for source, raison in briefing.indisponibles.items():
        print(f"\n[indisponible] {source} : {raison}")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv if argv is None else argv)
    commande = argv[1] if len(argv) > 1 else ""
    config = None if commande in ("", "aide", "--help", "-h", "version") else charger()

    if commande in ("aide", "--help", "-h"):
        print(AIDE)
        return 0
    if commande == "version":
        from . import VERSION
        print(VERSION)
        return 0
    if commande == "briefing-texte":
        return _briefing_texte(config)
    if commande == "outils":
        for outil in _moteur(config).lister():
            print(f"{outil.niveau.name.lower():8} {outil.nom:20} {outil.description}")
        return 0
    if commande == "journal":
        from .journal import Journal
        for entree in Journal(config.dossier_etat).lire(50):
            print(f"{entree.get('horodatage')}  {entree.get('decision', ''):9} {entree.get('outil')}  "
                  f"{entree.get('raison', '')}")
        return 0
    if commande in ("arret", "reprise"):
        from .permissions import activer_arret, lever_arret
        (activer_arret if commande == "arret" else lever_arret)(config)
        print("Arrêt d'urgence activé." if commande == "arret" else "L'IA peut de nouveau agir sur ce poste.")
        return 0
    if commande == "jeton":
        from .secret import enregistrer_jeton
        jeton = sys.stdin.readline().strip()
        if not jeton:
            print("Aucun jeton reçu sur l'entrée standard.", file=sys.stderr)
            return 1
        enregistrer_jeton(jeton)
        print("Jeton enregistré dans le trousseau.")
        return 0
    if commande == "mcp":
        from .mcp import servir
        servir(_moteur(config))
        return 0

    from .app import Application
    return Application().run(argv)


if __name__ == "__main__":
    sys.exit(main())
