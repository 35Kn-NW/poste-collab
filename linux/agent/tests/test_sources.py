import unittest
from datetime import date, datetime, timedelta

from poste_ia.sources import Briefing, Element, classer_taches, construire, enregistrer_cache, lire_cache
from poste_ia.sources.locale import TachesLocales

from .outils_test_base import PosteTemporaire

JOUR = date(2026, 10, 7)


class SourceFixe:
    def __init__(self, nom, briefing):
        self.nom, self._briefing = nom, briefing

    def briefing(self, jour):
        return self._briefing


class SourceEnPanne:
    nom = "IA métier"

    def briefing(self, jour):
        raise RuntimeError("non connectée à ce poste")


class TestBriefing(PosteTemporaire):
    def test_classement_des_taches(self):
        taches = [Element("Sans date"), Element("En retard", echeance=JOUR - timedelta(days=2)),
                  Element("Dans 3 jours", echeance=JOUR + timedelta(days=3)),
                  Element("Dans un mois", echeance=JOUR + timedelta(days=30))]
        briefing = classer_taches(JOUR, taches)
        self.assertEqual([e.titre for e in briefing.a_faire], ["Sans date", "En retard"])
        self.assertEqual(briefing.a_faire[1].priorite, "haute")
        self.assertEqual([e.titre for e in briefing.echeances], ["Dans 3 jours"])

    def test_une_source_en_panne_ne_bloque_pas(self):
        agenda = Briefing(jour=JOUR, rendez_vous=[Element("Signature Martin", debut=datetime(2026, 10, 7, 14, 30)),
                                                  Element("Rendez-vous Durand", debut=datetime(2026, 10, 7, 9, 0))])
        briefing = construire(JOUR, [SourceEnPanne(), SourceFixe("Agenda", agenda)])
        self.assertEqual(briefing.indisponibles, {"IA métier": "non connectée à ce poste"})
        self.assertEqual([e.titre for e in briefing.rendez_vous], ["Rendez-vous Durand", "Signature Martin"])
        self.assertTrue(briefing.resume().startswith("2 rendez-vous aujourd'hui, le premier à 09:00."))

    def test_vision_globale_et_synthese_ia(self):
        ia = Briefing(jour=JOUR, synthese="Journée chargée : 3 signatures.", indicateurs={"Dossiers en cours": 42})
        briefing = construire(JOUR, [SourceFixe("IA métier", ia)])
        self.assertEqual(briefing.resume(), "Journée chargée : 3 signatures.")
        self.assertIn(("Dossiers en cours", "42"), briefing.vue_globale())

    def test_cache(self):
        briefing = Briefing(jour=JOUR, a_verifier=[Element("Pièce manquante", echeance=JOUR, priorite="haute")])
        enregistrer_cache(briefing, self.config.dossier_donnees)
        relu = lire_cache(self.config.dossier_donnees, JOUR)
        self.assertEqual(relu.a_verifier[0].titre, "Pièce manquante")
        self.assertEqual(relu.a_verifier[0].echeance, JOUR)
        self.assertIsNone(lire_cache(self.config.dossier_donnees, JOUR + timedelta(days=1)))

    def test_taches_locales(self):
        taches = TachesLocales(self.config.dossier_donnees)
        tache = taches.ajouter("Appeler le géomètre")
        self.assertEqual(taches.briefing(JOUR).a_faire[0].titre, "Appeler le géomètre")
        taches.basculer(tache["id"], True)
        self.assertTrue(taches.briefing(date.today()).a_faire[0].fait)
        self.assertEqual(taches.briefing(date.today() + timedelta(days=1)).a_faire, [])

    def test_heure_avec_fuseau_ramenee_en_local(self):
        element = Element.depuis_dict({"titre": "RDV", "debut": "2026-10-07T12:00:00+00:00"})
        self.assertIsNone(element.debut.tzinfo)


if __name__ == "__main__":
    unittest.main()
