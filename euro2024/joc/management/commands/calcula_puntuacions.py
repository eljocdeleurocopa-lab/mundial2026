# -*- coding: utf-8 -*-
"""
Management command per calcular les puntuacions del Mundial FIFA 2026.

Ús:
    python manage.py calcula_puntuacions

Calcula totes les puntuacions de tots els jugadors i actualitza el rànquing.
"""

from django.core.management.base import BaseCommand
from django.db.models import F

from joc.models import (
    Jugador, Partit, PronosticPartit, PronosticEquipGrup, PronosticEquipFase,
    FASE_SETZENS, FASE_VUITENS, FASE_QUARTS, FASE_SEMIS, FASE_TERCER, FASE_FINAL,
)

# =============================================================================
# CONSTANTS DE PUNTUACIÓ
# =============================================================================

# --- Fase de grups: partits ---
PUNTS_SIGNE_GRUPS    = 3
PUNTS_RESULTAT_GRUPS = 4

# --- Fase de grups: classificació de grup ---
PUNTS_CLASSIFICACIO_GRUP = {1: 2, 2: 4, 4: 10}

# --- Setzens de final: equips classificats (32 encerts possibles) ---
PUNTS_EQUIPS_SETZENS = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
    7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1,
    13: 2, 14: 2, 15: 2, 16: 2,
    17: 4, 18: 4, 19: 4,
    20: 7, 21: 7,
    22: 10,
    23: 14,
    24: 18,
    25: 23,
    26: 28,
    27: 34,
    28: 40,
    29: 47,
    30: 55,
    31: 64,
    32: 75,
}

# --- Setzens de final: partits (sense punts per posició) ---
PUNTS_EQUIP_POSICIO_SETZENS = 0
PUNTS_SIGNE_SETZENS         = 5
PUNTS_RESULTAT_SETZENS      = 7

# --- Vuitens de final: equips classificats (16 encerts possibles) ---
PUNTS_EQUIPS_VUITENS = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
    7: 8, 8: 11, 9: 15, 10: 20,
    11: 26, 12: 33, 13: 41, 14: 50, 15: 60, 16: 75,
}

# --- Vuitens de final: partits (amb punts per posició, igual que quarts) ---
PUNTS_EQUIP_POSICIO_VUITENS = 5
PUNTS_SIGNE_VUITENS         = 5
PUNTS_RESULTAT_VUITENS      = 7

# --- Quarts de final: equips classificats (8 encerts possibles) ---
PUNTS_EQUIPS_QUARTS = {
    1: 3, 2: 6, 3: 10, 4: 17, 5: 27, 6: 40, 7: 55, 8: 75,
}

# --- Quarts de final: partits ---
PUNTS_EQUIP_POSICIO_QUARTS = 7
PUNTS_SIGNE_QUARTS         = 7
PUNTS_RESULTAT_QUARTS      = 10

# --- Semifinals: equips classificats (4 encerts possibles) ---
PUNTS_EQUIPS_SEMIS = {1: 8, 2: 20, 3: 40, 4: 75}

# --- Semifinals: partits ---
PUNTS_EQUIP_POSICIO_SEMIS = 10
PUNTS_SIGNE_SEMIS         = 10
PUNTS_RESULTAT_SEMIS      = 14

# --- Tercer i quart lloc: equips classificats ---
PUNTS_EQUIPS_TERCER = {1: 15, 2: 40}

# --- Tercer i quart lloc: partit ---
PUNTS_EQUIP_POSICIO_TERCER = 12
PUNTS_SIGNE_TERCER         = 14
PUNTS_RESULTAT_TERCER      = 20

# --- Final: equips classificats ---
PUNTS_EQUIPS_FINAL = {1: 30, 2: 75}

# --- Final: partit ---
PUNTS_EQUIP_POSICIO_FINAL = 15
PUNTS_SIGNE_FINAL         = 14
PUNTS_RESULTAT_FINAL      = 20

# --- Quadre final ---
PUNTS_QUADRE_FINAL = {1: 50, 2: 25, 3: 15, 4: 10}

# --- Rangs de partits per fase ---
RANG_PARTITS_GRUPS   = range(1,  73)   # partits  1–72
RANG_PARTITS_SETZENS = range(73, 89)   # partits 73–88
RANG_PARTITS_VUITENS = range(89, 97)   # partits 89–96
RANG_PARTITS_QUARTS  = range(97, 101)  # partits 97–100
RANG_PARTITS_SEMIS   = range(101, 103) # partits 101–102
ID_PARTIT_TERCER     = 103
ID_PARTIT_FINAL      = 104


# =============================================================================
# FUNCIONS AUXILIARS
# =============================================================================

def _punts_classificacio_grup(encerts):
    """Retorna els punts de classificació de grup segons els encerts."""
    return PUNTS_CLASSIFICACIO_GRUP.get(encerts, 0)


def _punts_equips_fase(encerts, taula):
    """Retorna els punts d'equips classificats per a una ronda donada."""
    return taula.get(encerts, 0)


def _punts_partit_grups(partit, pronostic):
    """
    Puntuació d'un partit de fase de grups.
    Resultat (4 pts) > Signe (3 pts) > res (0 pts). No acumulables.
    """
    if partit.resultat_encertat(pronostic):
        return PUNTS_RESULTAT_GRUPS
    elif partit.signe_encertat(pronostic):
        return PUNTS_SIGNE_GRUPS
    return 0


def _equips_correctes_pronostic(pronostic, partit):
    """
    Comprova si els 2 equips del pronòstic coincideixen amb els reals
    i en la posició correcta (equip1=local, equip2=visitant).
    Retorna (equip1_ok, equip2_ok).
    """
    equip1_ok = (pronostic.equip1_id == partit.equip1_id)
    equip2_ok = (pronostic.equip2_id == partit.equip2_id)
    return equip1_ok, equip2_ok


def _punts_partit_eliminatoria(partit, pronostic,
                                punts_posicio, punts_signe, punts_resultat):
    """
    Puntuació d'un partit de ronda eliminatòria.

    Regles:
    - Punts per posició d'equip s'acumulen sempre (si punts_posicio > 0).
    - Per puntuar signe o resultat, cal tenir els 2 equips en posició correcta.
    - Signe i resultat s'acumulen amb els punts de posició.
    - Signe i resultat no són acumulables entre ells (s'aplica el més alt).
    """
    equip1_ok, equip2_ok = _equips_correctes_pronostic(pronostic, partit)
    tots_ok = equip1_ok and equip2_ok
    encerts = (1 if equip1_ok else 0) + (1 if equip2_ok else 0)

    # Punts per posició (sempre s'acumulen)
    punts = punts_posicio * encerts

    # Punts per resultat o signe (només si els 2 equips són correctes)
    if tots_ok:
        if partit.resultat_encertat(pronostic):
            punts += punts_resultat
        elif partit.signe_encertat(pronostic):
            punts += punts_signe

    return punts


# =============================================================================
# CÀLCUL PER JUGADOR
# =============================================================================

def calcula_puntuacions_jugador(jugador):
    """
    Calcula totes les puntuacions d'un jugador i actualitza els seus camps.
    Retorna el total de punts.
    """

    # ----- 1. FASE DE GRUPS: PARTITS -----
    punts_resultats = 0
    partits_grups = Partit.objects.filter(
        pk__in=RANG_PARTITS_GRUPS,
        gols1__gte=0, gols2__gte=0,
    )
    for partit in partits_grups:
        try:
            pronostic = PronosticPartit.objects.get(jugador=jugador, partit=partit)
        except PronosticPartit.DoesNotExist:
            continue
        punts_resultats += _punts_partit_grups(partit, pronostic)

    # ----- 2. FASE DE GRUPS: CLASSIFICACIÓ -----
    punts_grups = 0
    grups_ids = PronosticEquipGrup.objects.filter(
        jugador=jugador
    ).values_list('equip__grup_id', flat=True).distinct()

    for grup_id in grups_ids:
        pronostics_grup = PronosticEquipGrup.objects.filter(
            jugador=jugador,
            equip__grup_id=grup_id,
            posicio__gt=0,
        )
        from django.conf import settings as django_settings
        try:
            admin_jugador = Jugador.objects.get(pk=django_settings.ID_ADMIN)
        except Jugador.DoesNotExist:
            continue

        encerts = 0
        for peg in pronostics_grup:
            try:
                real = PronosticEquipGrup.objects.get(
                    jugador=admin_jugador,
                    equip=peg.equip,
                )
                if real.posicio == peg.posicio:
                    encerts += 1
            except PronosticEquipGrup.DoesNotExist:
                pass

        punts_grups += _punts_classificacio_grup(encerts)

    # ----- 3. EQUIPS CLASSIFICATS PER RONDA -----
    punts_equips_encertats = 0

    encerts_setzens = _calcula_equips_encertats_fase(jugador, FASE_SETZENS)
    punts_equips_encertats += _punts_equips_fase(encerts_setzens, PUNTS_EQUIPS_SETZENS)

    encerts_vuitens = _calcula_equips_encertats_fase(jugador, FASE_VUITENS)
    punts_equips_encertats += _punts_equips_fase(encerts_vuitens, PUNTS_EQUIPS_VUITENS)

    encerts_quarts = _calcula_equips_encertats_fase(jugador, FASE_QUARTS)
    punts_equips_encertats += _punts_equips_fase(encerts_quarts, PUNTS_EQUIPS_QUARTS)

    encerts_semis = _calcula_equips_encertats_fase(jugador, FASE_SEMIS)
    punts_equips_encertats += _punts_equips_fase(encerts_semis, PUNTS_EQUIPS_SEMIS)

    encerts_tercer = _calcula_equips_encertats_fase(jugador, FASE_TERCER)
    punts_equips_encertats += _punts_equips_fase(encerts_tercer, PUNTS_EQUIPS_TERCER)

    encerts_final_equips = _calcula_equips_encertats_fase(jugador, FASE_FINAL)
    punts_equips_encertats += _punts_equips_fase(encerts_final_equips, PUNTS_EQUIPS_FINAL)

    # ----- 4. SETZENS: PARTITS -----
    punts_setzens = 0
    for id_partit in RANG_PARTITS_SETZENS:
        punts_setzens += _punts_ronda_eliminatoria(
            jugador, id_partit,
            punts_posicio=PUNTS_EQUIP_POSICIO_SETZENS,
            punts_signe=PUNTS_SIGNE_SETZENS,
            punts_resultat=PUNTS_RESULTAT_SETZENS,
        )

    # ----- 5. VUITENS: PARTITS -----
    punts_vuitens = 0
    for id_partit in RANG_PARTITS_VUITENS:
        punts_vuitens += _punts_ronda_eliminatoria(
            jugador, id_partit,
            punts_posicio=PUNTS_EQUIP_POSICIO_VUITENS,
            punts_signe=PUNTS_SIGNE_VUITENS,
            punts_resultat=PUNTS_RESULTAT_VUITENS,
        )

    # ----- 6. QUARTS: PARTITS -----
    punts_quarts = 0
    for id_partit in RANG_PARTITS_QUARTS:
        punts_quarts += _punts_ronda_eliminatoria(
            jugador, id_partit,
            punts_posicio=PUNTS_EQUIP_POSICIO_QUARTS,
            punts_signe=PUNTS_SIGNE_QUARTS,
            punts_resultat=PUNTS_RESULTAT_QUARTS,
        )

    # ----- 7. SEMIS: PARTITS -----
    punts_semis = 0
    for id_partit in RANG_PARTITS_SEMIS:
        punts_semis += _punts_ronda_eliminatoria(
            jugador, id_partit,
            punts_posicio=PUNTS_EQUIP_POSICIO_SEMIS,
            punts_signe=PUNTS_SIGNE_SEMIS,
            punts_resultat=PUNTS_RESULTAT_SEMIS,
        )

    # ----- 8. TERCER I QUART LLOC: PARTIT -----
    punts_tercer = _punts_ronda_eliminatoria(
        jugador, ID_PARTIT_TERCER,
        punts_posicio=PUNTS_EQUIP_POSICIO_TERCER,
        punts_signe=PUNTS_SIGNE_TERCER,
        punts_resultat=PUNTS_RESULTAT_TERCER,
    )

    # ----- 9. FINAL: PARTIT -----
    punts_final = _punts_ronda_eliminatoria(
        jugador, ID_PARTIT_FINAL,
        punts_posicio=PUNTS_EQUIP_POSICIO_FINAL,
        punts_signe=PUNTS_SIGNE_FINAL,
        punts_resultat=PUNTS_RESULTAT_FINAL,
    )

    # ----- 10. QUADRE FINAL -----
    punts_quadre_final = _calcula_quadre_final(jugador)

    # ----- TOTAL -----
    total = (
        punts_resultats
        + punts_grups
        + punts_equips_encertats
        + punts_setzens
        + punts_vuitens
        + punts_quarts
        + punts_semis
        + punts_tercer
        + punts_final
        + punts_quadre_final
    )

    jugador.punts_anterior         = jugador.punts
    jugador.punts                  = total
    jugador.punts_resultats        = punts_resultats
    jugador.punts_grups            = punts_grups
    jugador.punts_equips_encertats = punts_equips_encertats
    jugador.punts_setzens          = punts_setzens
    jugador.punts_vuitens          = punts_vuitens
    jugador.punts_quarts           = punts_quarts
    jugador.punts_semis            = punts_semis
    jugador.punts_tercer           = punts_tercer
    jugador.punts_final            = punts_final
    jugador.punts_quadre_final     = punts_quadre_final
    jugador.save()

    return total


def _calcula_equips_encertats_fase(jugador, fase):
    """
    Compta quants equips ha encertat el jugador per a una fase donada,
    comparant amb els pronòstics de l'admin (ID_ADMIN).
    """
    from django.conf import settings as django_settings
    try:
        admin_jugador = Jugador.objects.get(pk=django_settings.ID_ADMIN)
    except Jugador.DoesNotExist:
        return 0

    equips_admin = set(
        PronosticEquipFase.objects.filter(
            jugador=admin_jugador, fase=fase
        ).values_list('equip_id', flat=True)
    )
    equips_jugador = set(
        PronosticEquipFase.objects.filter(
            jugador=jugador, fase=fase
        ).values_list('equip_id', flat=True)
    )
    return len(equips_admin & equips_jugador)


def _punts_ronda_eliminatoria(jugador, id_partit,
                               punts_posicio, punts_signe, punts_resultat):
    """
    Obté la puntuació d'un partit eliminatori per a un jugador.
    Retorna 0 si el partit no s'ha jugat o no hi ha pronòstic.
    """
    try:
        partit = Partit.objects.get(pk=id_partit)
    except Partit.DoesNotExist:
        return 0

    if partit.gols1 < 0 or partit.gols2 < 0:
        return 0

    try:
        pronostic = PronosticPartit.objects.get(jugador=jugador, partit=partit)
    except PronosticPartit.DoesNotExist:
        return 0

    return _punts_partit_eliminatoria(
        partit, pronostic, punts_posicio, punts_signe, punts_resultat
    )


def _calcula_quadre_final(jugador):
    """
    Calcula els punts del quadre final (campió, subcampió, 3r, 4t).
    Compara les posicions del jugador amb les de l'admin.
    """
    from django.conf import settings as django_settings
    try:
        admin_jugador = Jugador.objects.get(pk=django_settings.ID_ADMIN)
    except Jugador.DoesNotExist:
        return 0

    punts = 0

    for fase in [FASE_FINAL, FASE_TERCER]:
        pronostics_admin = {
            pef.equip_id: pef.posicio
            for pef in PronosticEquipFase.objects.filter(
                jugador=admin_jugador, fase=fase
            )
        }
        pronostics_jugador = {
            pef.equip_id: pef.posicio
            for pef in PronosticEquipFase.objects.filter(
                jugador=jugador, fase=fase
            )
        }
        for equip_id, posicio_admin in pronostics_admin.items():
            posicio_jugador = pronostics_jugador.get(equip_id)
            if posicio_jugador == posicio_admin:
                punts += PUNTS_QUADRE_FINAL.get(posicio_admin, 0)

    return punts


# =============================================================================
# ACTUALITZACIÓ DEL RÀNQUING
# =============================================================================

def actualitza_ranking():
    """
    Ordena tots els jugadors per punts (descendent) i assigna les posicions.
    """
    jugadors = list(Jugador.objects.all().order_by('-punts', 'id'))
    for i, jugador in enumerate(jugadors):
        jugador.posicio_anterior = jugador.posicio
        jugador.posicio = i + 1
        jugador.save(update_fields=['posicio', 'posicio_anterior'])


# =============================================================================
# MANAGEMENT COMMAND
# =============================================================================

class Command(BaseCommand):
    help = 'Calcula les puntuacions de tots els jugadors i actualitza el rànquing'

    def handle(self, *args, **options):
        from django.conf import settings as django_settings

        jugadors = Jugador.objects.exclude(pk=django_settings.ID_ADMIN)
        total_jugadors = jugadors.count()

        self.stdout.write(f'Calculant puntuacions per a {total_jugadors} jugadors...')

        for jugador in jugadors:
            punts = calcula_puntuacions_jugador(jugador)
            self.stdout.write(f'  {jugador.usuari.username}: {punts} punts')

        self.stdout.write('Actualitzant rànquing...')
        actualitza_ranking()

        self.stdout.write(self.style.SUCCESS(
            f'Puntuacions calculades correctament per a {total_jugadors} jugadors.'
        ))
