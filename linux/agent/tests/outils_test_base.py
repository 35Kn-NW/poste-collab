"""Poste fictif dans un dossier temporaire, commun aux tests."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from poste_ia import config as module_config
from poste_ia.config import Config


class PosteTemporaire(unittest.TestCase):
    def setUp(self):
        self._temporaire = tempfile.TemporaryDirectory()
        self.racine = Path(self._temporaire.name).resolve()
        self.documents = self.racine / "Documents"
        (self.documents / "Dossier Dupont").mkdir(parents=True)
        (self.documents / "Dossier Dupont" / "compromis.txt").write_text("Compromis de vente Dupont", encoding="utf-8")
        (self.documents / ".cache").mkdir()
        (self.documents / ".cache" / "secret.txt").write_text("caché", encoding="utf-8")
        self.config = Config(dossiers_autorises=[str(self.documents)],
                             dossier_brouillons=str(self.documents / "Brouillons IA"),
                             dossier_etat=self.racine / "etat", dossier_donnees=self.racine / "donnees")
        correctif = mock.patch.object(module_config, "ARRET_SYSTEME", self.racine / "arret-systeme-absent")
        correctif.start()
        self.addCleanup(correctif.stop)

    def tearDown(self):
        self._temporaire.cleanup()
