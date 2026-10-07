"""Agenda et tâches d'Evolution (Evolution Data Server), lus en local sur le poste."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from . import Briefing, Element, classer_taches


def _modules():
    import gi
    gi.require_version("EDataServer", "1.2")
    gi.require_version("ECal", "2.0")
    gi.require_version("ICalGLib", "3.0")
    from gi.repository import ECal, EDataServer, ICalGLib
    return ECal, EDataServer, ICalGLib


def _liste(resultat):
    # Selon la version de PyGObject : la liste seule, ou (succès, liste).
    return resultat[1] if isinstance(resultat, tuple) else (resultat or [])


def _texte(composant_texte) -> str:
    return composant_texte.get_value() if composant_texte else ""


def _instant(valeur_cal, ICalGLib):
    """ECal.ComponentDateTime vers datetime local (None pour une journée entière)."""
    if valeur_cal is None:
        return None
    horaire = valeur_cal.get_value()
    if horaire is None or horaire.is_null_time() or horaire.is_date():
        return None
    zone = horaire.get_timezone()
    if zone is None and valeur_cal.get_tzid():
        zone = ICalGLib.Timezone.get_builtin_timezone_from_tzid(valeur_cal.get_tzid())
    if zone is not None or horaire.is_utc():
        secondes = horaire.as_timet_with_zone(zone or ICalGLib.Timezone.get_utc_timezone())
        return datetime.fromtimestamp(secondes)
    return datetime(horaire.get_year(), horaire.get_month(), horaire.get_day(),
                    horaire.get_hour(), horaire.get_minute())


def _jour(valeur_cal):
    if valeur_cal is None or valeur_cal.get_value() is None:
        return None
    horaire = valeur_cal.get_value()
    return date(horaire.get_year(), horaire.get_month(), horaire.get_day())


class AgendaEvolution:
    nom = "Agenda Evolution"

    def briefing(self, jour: date) -> Briefing:
        ECal, EDataServer, ICalGLib = _modules()
        registre = EDataServer.SourceRegistry.new_sync(None)
        debut = datetime.combine(jour, time.min).astimezone(timezone.utc)
        fin = debut + timedelta(days=1)
        filtre = (f'(occur-in-time-range? (make-time "{debut:%Y%m%dT%H%M%SZ}") '
                  f'(make-time "{fin:%Y%m%dT%H%M%SZ}"))')
        briefing = Briefing(jour=jour)
        for source in registre.list_enabled(EDataServer.SOURCE_EXTENSION_CALENDAR):
            client = ECal.Client.connect_sync(source, ECal.ClientSourceType.EVENTS, 15, None)
            for composant in _liste(client.get_object_list_as_comps_sync(filtre, None)):
                commence = _instant(composant.get_dtstart(), ICalGLib)
                termine = _instant(composant.get_dtend(), ICalGLib)
                if commence and commence.date() != jour:
                    # Occurrence d'un rendez-vous répétitif : même heure, ce jour-là.
                    duree = (termine - commence) if termine else None
                    commence = datetime.combine(jour, commence.time())
                    termine = commence + duree if duree else None
                briefing.rendez_vous.append(Element(
                    titre=_texte(composant.get_summary()) or "(sans titre)",
                    detail=composant.get_location() or "",
                    debut=commence, fin=termine, source=self.nom, ident=composant.get_uid() or ""))
        taches = []
        for source in registre.list_enabled(EDataServer.SOURCE_EXTENSION_TASK_LIST):
            client = ECal.Client.connect_sync(source, ECal.ClientSourceType.TASKS, 15, None)
            for composant in _liste(client.get_object_list_as_comps_sync("(not (is-completed?))", None)):
                priorite = composant.get_priority() if hasattr(composant, "get_priority") else 0
                taches.append(Element(
                    titre=_texte(composant.get_summary()) or "(sans titre)",
                    echeance=_jour(composant.get_due()),
                    priorite="haute" if priorite and 0 < priorite <= 4 else "normale",
                    source=self.nom, ident=composant.get_uid() or ""))
        briefing.fusionner(classer_taches(jour, taches))
        return briefing
