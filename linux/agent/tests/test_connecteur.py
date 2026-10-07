import json
import threading
import unittest
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from poste_ia.config import Config
from poste_ia.sources.connecteur import Connecteur, ConnecteurIndisponible
from poste_ia.sources.ia import SourceIA

RECU = {}


class ServeurIAFictif(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _json(self, code, donnees=None):
        corps = b"" if donnees is None else json.dumps(donnees).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        RECU["autorisation"] = self.headers.get("Authorization")
        if self.path.startswith("/poste/v1/briefing?date=2026-10-07"):
            self._json(200, {"synthese": "Trois signatures aujourd'hui.", "indicateurs": {"Dossiers en cours": 42},
                             "rendez_vous": [{"id": "r1", "titre": "Signature Dupont",
                                              "debut": "2026-10-07T10:00:00", "fin": "2026-10-07T11:00:00"}],
                             "a_verifier": [{"titre": "Diagnostic amiante manquant", "priorite": "haute"}]})
        elif self.path.startswith("/poste/v1/outils/attente"):
            self._json(204)
        else:
            self._json(404, {"erreur": "inconnu"})

    def do_POST(self):
        corps = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/poste/v1/conversation":
            RECU["messages"] = corps["messages"]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for morceau in ("Bonjour", ", maître."):
                self.wfile.write(f"data: {json.dumps({'delta': morceau})}\n\n".encode())
            self.wfile.write(b"data: [DONE]\n\n")
        elif self.path == "/poste/v1/outils/resultat":
            RECU["resultat"] = corps
            self._json(200, {})
        else:
            self._json(404)


class TestConnecteur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serveur = ThreadingHTTPServer(("127.0.0.1", 0), ServeurIAFictif)
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.serveur.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()

    def connecteur(self, url=None):
        return Connecteur(Config(connecteur_url=url or self.url), jeton="jeton-test")

    def test_briefing_et_source_ia(self):
        briefing = SourceIA(self.connecteur()).briefing(date(2026, 10, 7))
        self.assertEqual(RECU["autorisation"], "Bearer jeton-test")
        self.assertEqual(briefing.synthese, "Trois signatures aujourd'hui.")
        self.assertEqual(briefing.rendez_vous[0].debut.hour, 10)
        self.assertEqual(briefing.a_verifier[0].priorite, "haute")
        self.assertEqual(briefing.indicateurs["Dossiers en cours"], 42)

    def test_conversation_en_flux(self):
        morceaux = list(self.connecteur().converser([{"role": "user", "content": "Bonjour"}]))
        self.assertEqual("".join(morceaux), "Bonjour, maître.")
        self.assertEqual(RECU["messages"][0]["content"], "Bonjour")

    def test_outils(self):
        connecteur = self.connecteur()
        self.assertIsNone(connecteur.appel_outil_suivant(attente=1))
        connecteur.envoyer_resultat("a1", {"ok": True})
        self.assertEqual(RECU["resultat"], {"id": "a1", "resultat": {"ok": True}, "erreur": None})

    def test_non_configure_ou_injoignable(self):
        with self.assertRaises(ConnecteurIndisponible):
            Connecteur(Config()).briefing(date(2026, 10, 7))
        with self.assertRaises(ConnecteurIndisponible):
            self.connecteur("http://127.0.0.1:9").briefing(date(2026, 10, 7))


if __name__ == "__main__":
    unittest.main()
