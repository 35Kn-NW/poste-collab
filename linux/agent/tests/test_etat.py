import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from poste_ia.config import Config
from poste_ia.etat import (DEGRADE, ERREUR, INACTIF, OK, Sondes, interfaces_vpn, joignable_tcp, publier)
from poste_ia.sources.connecteur import ConnecteurIndisponible


class TestEtat(unittest.TestCase):
    def setUp(self):
        self._temporaire = tempfile.TemporaryDirectory()
        self.racine = Path(self._temporaire.name)
        self.reseau = self.racine / "net"
        self.sources = self.racine / "sources"
        self.sources.mkdir()
        self.ecoute = socket.socket()
        self.ecoute.bind(("127.0.0.1", 0))
        self.ecoute.listen()
        self.port = self.ecoute.getsockname()[1]

    def tearDown(self):
        self.ecoute.close()
        self._temporaire.cleanup()

    def interface(self, nom, etat="unknown", uevent=""):
        dossier = self.reseau / nom
        dossier.mkdir(parents=True)
        (dossier / "operstate").write_text(etat)
        (dossier / "uevent").write_text(uevent)

    def sondes(self, sondes=None, connecteur=None, https=lambda _url: True):
        config = Config(sondes=sondes or {})
        connecteur = connecteur or mock.Mock(actif=False)
        return Sondes(config, connecteur, racine_reseau=self.reseau, sources_evolution=self.sources, https=https)

    def test_tcp(self):
        self.assertTrue(joignable_tcp("127.0.0.1", self.port))
        self.assertFalse(joignable_tcp("127.0.0.1", 9, delai=0.5))

    def test_real_et_base(self):
        sondes = self.sondes({"real": {"hote": "127.0.0.1", "port": self.port},
                              "base": {"hote": "127.0.0.1", "port": 9}})
        self.assertEqual(sondes.real().niveau, OK)
        self.assertEqual(sondes.base().niveau, ERREUR)
        self.assertEqual(self.sondes().real().niveau, INACTIF)

    def test_ia(self):
        self.assertEqual(self.sondes().ia().niveau, INACTIF)
        connecteur = mock.Mock(actif=True)
        self.assertEqual(self.sondes(connecteur=connecteur).ia().niveau, OK)
        connecteur.etat.side_effect = ConnecteurIndisponible("serveur injoignable")
        self.assertEqual(self.sondes(connecteur=connecteur).ia().niveau, ERREUR)

    def test_office_365(self):
        self.assertEqual(self.sondes(https=lambda _u: False).m365().niveau, ERREUR)
        self.assertEqual(self.sondes().m365().niveau, DEGRADE)
        (self.sources / "compte.source").write_text("[Collection]\nBackendName=microsoft365\n")
        self.assertEqual(self.sondes().m365().niveau, OK)

    def test_vpn(self):
        self.interface("eth0", "up")
        self.interface("lo", "unknown")
        self.assertEqual(interfaces_vpn(self.reseau), [])
        self.assertEqual(self.sondes().vpn().niveau, INACTIF)
        au_bureau = self.sondes({"bureau": {"hote": "127.0.0.1", "port": self.port}})
        self.assertEqual(au_bureau.vpn().detail, "au bureau : VPN inutile")
        a_distance = self.sondes({"bureau": {"hote": "127.0.0.1", "port": 9}})
        self.assertEqual(a_distance.vpn().niveau, DEGRADE)
        self.interface("etude0", "unknown", "DEVTYPE=wireguard")
        self.assertEqual(a_distance.vpn().niveau, OK)
        self.interface("tun0", "down")
        self.assertEqual(interfaces_vpn(self.reseau), ["etude0"])

    def test_mesure_complete_et_publication(self):
        etat = self.sondes().mesurer()
        self.assertEqual(list(etat["services"]), ["real", "ia", "m365", "vpn", "base"])
        self.assertEqual(etat["services"]["m365"]["libelle"], "Office 365")
        chemin = publier(etat, self.racine / "run" / "etat.json")
        self.assertIn("horodatage", chemin.read_text())


if __name__ == "__main__":
    unittest.main()
