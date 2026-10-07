import unittest
from unittest import mock

from poste_ia.journal import Journal
from poste_ia.outils import Moteur
from poste_ia.permissions import ArretUrgence, Refus, activer_arret, lever_arret

from .outils_test_base import PosteTemporaire


class TestOutils(PosteTemporaire):
    def moteur(self, confirmer=lambda _q: False, connecteur=None):
        self.notifications = []
        return Moteur(self.config, Journal(self.config.dossier_etat), confirmer=confirmer,
                      notifier=lambda t, x: self.notifications.append((t, x)), connecteur=connecteur)

    def test_lister_dans_le_perimetre(self):
        resultat = self.moteur().executer("fichiers_lister", {"dossier": str(self.documents)})
        noms = [e["nom"] for e in resultat["elements"]]
        self.assertEqual(noms, ["Dossier Dupont"])  # les éléments cachés n'apparaissent pas

    def test_hors_perimetre_refuse(self):
        with self.assertRaises(Refus):
            self.moteur().executer("fichier_lire", {"chemin": "/etc/passwd"})

    def test_element_cache_refuse(self):
        with self.assertRaises(Refus):
            self.moteur().executer("fichier_lire", {"chemin": str(self.documents / ".cache" / "secret.txt")})

    def test_lien_symbolique_vers_l_exterieur_refuse(self):
        (self.documents / "raccourci").symlink_to("/etc")
        with self.assertRaises(Refus):
            self.moteur().executer("fichier_lire", {"chemin": str(self.documents / "raccourci" / "hostname")})

    def test_lire_et_chercher(self):
        moteur = self.moteur()
        lu = moteur.executer("fichier_lire", {"chemin": str(self.documents / "Dossier Dupont" / "compromis.txt")})
        self.assertIn("Compromis", lu["texte"])
        trouve = moteur.executer("fichiers_chercher", {"motif": "compromis"})
        self.assertEqual(len(trouve["resultats"]), 1)
        self.assertEqual(moteur.executer("fichiers_chercher", {"motif": "secret"})["resultats"], [])

    def test_brouillon_ne_remplace_jamais(self):
        moteur = self.moteur()
        premier = moteur.executer("brouillon_ecrire", {"nom": "Réponse Dupont", "contenu": "v1"})
        second = moteur.executer("brouillon_ecrire", {"nom": "Réponse Dupont", "contenu": "v2"})
        self.assertNotEqual(premier["chemin"], second["chemin"])
        self.assertTrue(second["chemin"].endswith("Réponse Dupont (2).txt"))
        self.assertEqual(len(self.notifications), 2)  # chaque action est signalée

    def test_courriel_prepare_sans_envoi(self):
        with mock.patch("poste_ia.outils.subprocess.Popen") as lancer:
            resultat = self.moteur().executer("courriel_preparer",
                                              {"destinataires": "client@example.org", "objet": "Rendez-vous",
                                               "corps": "Bonjour"})
        self.assertFalse(resultat["envoye"])
        self.assertTrue(lancer.call_args[0][0][1].startswith("mailto:client@example.org?subject=Rendez-vous"))

    def test_engager_exige_confirmation(self):
        moteur = self.moteur(confirmer=lambda _q: False)
        with self.assertRaises(Refus):
            moteur.executer("document_sceller", {"chemin": str(self.documents / "Dossier Dupont" / "compromis.txt")})
        self.assertEqual(moteur.journal.lire()[-1]["decision"], "refuse")

    def test_engager_confirme_mais_sans_connecteur(self):
        moteur = self.moteur(confirmer=lambda _q: True)
        with self.assertRaises(Refus):
            moteur.executer("document_sceller", {"chemin": str(self.documents / "Dossier Dupont" / "compromis.txt")})

    def test_engager_confirme_avec_connecteur(self):
        connecteur = mock.Mock(actif=True)
        connecteur.sceller.return_value = {"ancre": "ok"}
        moteur = self.moteur(confirmer=lambda _q: True, connecteur=connecteur)
        resultat = moteur.executer("document_sceller",
                                   {"chemin": str(self.documents / "Dossier Dupont" / "compromis.txt")})
        self.assertEqual(resultat, {"ancre": "ok"})
        empreinte, nom = connecteur.sceller.call_args[0]
        self.assertEqual(len(empreinte), 64)
        self.assertEqual(nom, "compromis.txt")

    def test_arret_urgence(self):
        moteur = self.moteur()
        activer_arret(self.config)
        with self.assertRaises(ArretUrgence):
            moteur.executer("fichiers_chercher", {"motif": "x"})
        lever_arret(self.config)
        moteur.executer("fichiers_chercher", {"motif": "x"})
        self.assertEqual([e["decision"] for e in moteur.journal.lire()], ["arret", "execute"])

    def test_parametres_invalides(self):
        with self.assertRaises(Refus):
            self.moteur().executer("fichiers_chercher", {"motif": "x", "inattendu": 1})
        with self.assertRaises(Refus):
            self.moteur().executer("fichiers_chercher", {})

    def test_outil_inconnu(self):
        with self.assertRaises(Refus):
            self.moteur().executer("formater_disque", {})


if __name__ == "__main__":
    unittest.main()
