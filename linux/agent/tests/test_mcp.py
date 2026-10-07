import io
import json
import unittest

from poste_ia.journal import Journal
from poste_ia.mcp import servir, traiter
from poste_ia.outils import Moteur

from .outils_test_base import PosteTemporaire


class TestMCP(PosteTemporaire):
    def setUp(self):
        super().setUp()
        self.moteur = Moteur(self.config, Journal(self.config.dossier_etat), confirmer=lambda _q: False,
                             notifier=lambda *_: None)

    def test_initialisation_et_liste(self):
        init = traiter(self.moteur, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                     "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(init["result"]["serverInfo"]["name"], "poste-ia")
        self.assertIn("tools", init["result"]["capabilities"])
        outils = traiter(self.moteur, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        noms = {o["name"] for o in outils}
        self.assertIn("fichiers_chercher", noms)
        self.assertEqual(outils[0]["inputSchema"]["type"], "object")

    def test_appel_reussi_et_refuse(self):
        ok = traiter(self.moteur, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                   "params": {"name": "fichiers_chercher", "arguments": {"motif": "compromis"}}})
        self.assertFalse(ok["result"]["isError"])
        self.assertIn("compromis.txt", json.loads(ok["result"]["content"][0]["text"])["resultats"][0])
        refus = traiter(self.moteur, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                      "params": {"name": "fichier_lire", "arguments": {"chemin": "/etc/passwd"}}})
        self.assertTrue(refus["result"]["isError"])

    def test_notification_et_methode_inconnue(self):
        self.assertIsNone(traiter(self.moteur, {"jsonrpc": "2.0", "method": "notifications/initialized"}))
        inconnue = traiter(self.moteur, {"jsonrpc": "2.0", "id": 5, "method": "resources/list"})
        self.assertEqual(inconnue["error"]["code"], -32601)

    def test_transport_stdio(self):
        entree = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\nnon-json\n')
        sortie = io.StringIO()
        servir(self.moteur, entree, sortie)
        lignes = [json.loads(l) for l in sortie.getvalue().splitlines()]
        self.assertEqual(lignes[0]["result"], {})
        self.assertEqual(lignes[1]["error"]["code"], -32700)


if __name__ == "__main__":
    unittest.main()
