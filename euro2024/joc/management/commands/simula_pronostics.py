# -*- coding: utf-8 -*-
"""
Management command per simular pronòstics i verificar el sistema de puntuació.

Ús:
    python manage.py simula_pronostics

Genera pronòstics per als usuaris prova1-prova4, resultats reals fictícis,
calcula els punts i mostra un informe detallat.

ATENCIÓ: Esborra els pronòstics i resultats existents dels usuaris de prova.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

from joc.models import (
    Jugador, Partit, Equip, Grup,
    PronosticPartit, PronosticEquipGrup, PronosticEquipFase,
    FASE_SETZENS, FASE_VUITENS, FASE_QUARTS, FASE_SEMIS, FASE_TERCER, FASE_FINAL,
)
from joc.management.commands.calcula_puntuacions import (
    calcula_puntuacions_jugador, actualitza_ranking
)


# =============================================================================
# RESULTATS REALS FICTÍCIS (fase de grups, partits 1-72)
# Format: {id_partit: (gols1, gols2)}
# =============================================================================
RESULTATS_GRUPS = {
    1:  (2, 0),  2:  (1, 1),  3:  (3, 1),  4:  (2, 2),
    5:  (0, 1),  6:  (1, 2),  7:  (0, 0),  8:  (1, 3),
    9:  (2, 1),  10: (1, 0),  11: (2, 2),  12: (0, 1),
    13: (3, 0),  14: (1, 1),  15: (0, 2),  16: (1, 0),
    17: (2, 0),  18: (1, 1),  19: (3, 2),  20: (0, 1),
    21: (1, 0),  22: (2, 1),  23: (0, 2),  24: (1, 1),
    25: (0, 1),  26: (2, 0),  27: (1, 2),  28: (1, 0),
    29: (3, 1),  30: (0, 1),  31: (2, 0),  32: (1, 1),
    33: (0, 2),  34: (1, 1),  35: (2, 0),  36: (0, 1),
    37: (1, 0),  38: (2, 1),  39: (0, 0),  40: (1, 2),
    41: (3, 0),  42: (1, 1),  43: (0, 2),  44: (1, 0),
    45: (2, 1),  46: (1, 0),  47: (0, 1),  48: (2, 2),
    49: (1, 0),  50: (0, 2),  51: (1, 1),  52: (2, 0),
    53: (0, 1),  54: (1, 2),  55: (2, 1),  56: (0, 0),
    57: (1, 1),  58: (2, 0),  59: (0, 1),  60: (1, 2),
    61: (3, 1),  62: (0, 0),  63: (1, 1),  64: (0, 2),
    65: (2, 0),  66: (1, 1),  67: (0, 2),  68: (1, 0),
    69: (2, 1),  70: (0, 1),  71: (1, 0),  72: (2, 2),
}

# Resultats rondes eliminatòries (empat=1 vol dir guanya equip1)
RESULTATS_ELIM = {
    # Setzens (73-88)
    73: (1, 0, None), 74: (2, 1, None), 75: (0, 1, None), 76: (1, 1, 1),
    77: (2, 0, None), 78: (1, 2, None), 79: (0, 0, 2),    80: (1, 0, None),
    81: (2, 1, None), 82: (0, 1, None), 83: (1, 1, 2),    84: (2, 0, None),
    85: (1, 0, None), 86: (0, 2, None), 87: (1, 1, 1),    88: (2, 1, None),
    # Vuitens (89-96)
    89: (1, 0, None), 90: (2, 1, None), 91: (0, 1, None), 92: (1, 1, 1),
    93: (2, 0, None), 94: (1, 2, None), 95: (1, 1, 2),    96: (2, 0, None),
    # Quarts (97-100)
    97: (1, 0, None), 98: (2, 1, None), 99: (0, 1, None), 100: (1, 1, 1),
    # Semis (101-102)
    101: (2, 0, None), 102: (1, 2, None),
    # Tercer (103)
    103: (1, 0, None),
    # Final (104)
    104: (2, 1, None),
}


def _signe(g1, g2):
    if g1 > g2: return 1
    if g2 > g1: return 2
    return 0


class Command(BaseCommand):
    help = 'Simula pronòstics i verifica el sistema de puntuació'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('SIMULACIÓ DE PUNTUACIÓ - El Joc del Mundial 2026')
        self.stdout.write('=' * 60)

        # Obtenim els usuaris de prova
        usuaris = ['prova1', 'prova2', 'prova3', 'prova4']
        jugadors = []
        for nom in usuaris:
            try:
                user = User.objects.get(username=nom)
                jugador = Jugador.objects.get(usuari=user)
                jugadors.append(jugador)
                self.stdout.write(f'✓ Trobat usuari: {nom}')
            except (User.DoesNotExist, Jugador.DoesNotExist):
                self.stdout.write(f'✗ No trobat usuari: {nom} — crea\'l primer a l\'app')
                return

        # Obtenim l'admin
        try:
            admin = Jugador.objects.get(pk=settings.ID_ADMIN)
            self.stdout.write(f'✓ Admin: {admin.usuari.username}')
        except Jugador.DoesNotExist:
            self.stdout.write('✗ No trobat admin (ID_ADMIN)')
            return

        self.stdout.write('')
        self.stdout.write('--- FASE 1: Entrant resultats reals ---')

        # Entrem resultats reals als partits
        for id_partit, (g1, g2) in RESULTATS_GRUPS.items():
            try:
                partit = Partit.objects.get(pk=id_partit)
                partit.gols1 = g1
                partit.gols2 = g2
                partit.save()
            except Partit.DoesNotExist:
                self.stdout.write(f'  ✗ Partit {id_partit} no trobat')

        for id_partit, (g1, g2, empat) in RESULTATS_ELIM.items():
            try:
                partit = Partit.objects.get(pk=id_partit)
                # Per eliminatòries cal tenir equips assignats
                if partit.equip1 and partit.equip2:
                    partit.gols1 = g1
                    partit.gols2 = g2
                    partit.empat = empat
                    partit.save()
            except Partit.DoesNotExist:
                pass

        self.stdout.write('✓ Resultats reals entrats (72 partits de grups)')

        # Entrem pronòstics de l'admin (resultats reals)
        self.stdout.write('')
        self.stdout.write('--- FASE 2: Entrant pronòstics de l\'admin ---')
        self._entra_pronostics_admin(admin)
        self.stdout.write('✓ Pronòstics admin entrats')

        # Entrem pronòstics dels 4 usuaris
        self.stdout.write('')
        self.stdout.write('--- FASE 3: Entrant pronòstics usuaris de prova ---')

        estrategies = [
            'PERFECTE (encerta tot)',
            'SIGNE (encerta signe, no resultat)',
            'MIXT (alguns resultats, alguns signes)',
            'DOLENT (encerta poc)',
        ]

        for i, jugador in enumerate(jugadors):
            self._entra_pronostics_usuari(jugador, i, admin)
            self.stdout.write(f'✓ {jugador.usuari.username}: {estrategies[i]}')

        # Classifiquem els grups per l'admin
        self.stdout.write('')
        self.stdout.write('--- FASE 4: Classificació de grups (admin) ---')
        self._classifica_grups(admin)
        self.stdout.write('✓ Classificació de grups admin entrada')

        # Classifiquem els grups per als usuaris
        for i, jugador in enumerate(jugadors):
            self._classifica_grups_usuari(jugador, i, admin)
        self.stdout.write('✓ Classificació de grups usuaris entrada')

        # Calculem punts
        self.stdout.write('')
        self.stdout.write('--- FASE 5: Calculant puntuacions ---')
        for jugador in jugadors:
            calcula_puntuacions_jugador(jugador)
        actualitza_ranking()
        self.stdout.write('✓ Puntuacions calculades')

        # Informe
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('INFORME DE PUNTUACIONS')
        self.stdout.write('=' * 60)

        for jugador in jugadors:
            jugador.refresh_from_db()
            self.stdout.write(f'\n{jugador.usuari.username} ({estrategies[jugadors.index(jugador)]}):')
            self.stdout.write(f'  Partits grups:       {jugador.punts_resultats} pts')
            self.stdout.write(f'  Classificació grups: {jugador.punts_grups} pts')
            self.stdout.write(f'  Equips encertats:    {jugador.punts_equips_encertats} pts')
            self.stdout.write(f'  Setzens:             {jugador.punts_setzens} pts')
            self.stdout.write(f'  Vuitens:             {jugador.punts_vuitens} pts')
            self.stdout.write(f'  Quarts:              {jugador.punts_quarts} pts')
            self.stdout.write(f'  Semis:               {jugador.punts_semis} pts')
            self.stdout.write(f'  Tercer:              {jugador.punts_tercer} pts')
            self.stdout.write(f'  Final:               {jugador.punts_final} pts')
            self.stdout.write(f'  Quadre final:        {jugador.punts_quadre_final} pts')
            self.stdout.write(f'  TOTAL:               {jugador.punts} pts')

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('Simulació completada.')
        self.stdout.write('IMPORTANT: Els resultats reals fictícis han quedat')
        self.stdout.write('guardats a la BD. Esborra\'ls amb:')
        self.stdout.write('  python manage.py esborra_simulacio')
        self.stdout.write('=' * 60)

    def _entra_pronostics_admin(self, admin):
        """L'admin entra els resultats reals com a pronòstics."""
        for id_partit, (g1, g2) in RESULTATS_GRUPS.items():
            try:
                partit = Partit.objects.get(pk=id_partit)
                pron, _ = PronosticPartit.objects.get_or_create(
                    jugador=admin, partit=partit,
                    defaults={'equip1': partit.equip1, 'equip2': partit.equip2}
                )
                pron.gols1 = g1
                pron.gols2 = g2
                pron.save()
            except Partit.DoesNotExist:
                pass

    def _entra_pronostics_usuari(self, jugador, index, admin):
        """Entra pronòstics segons l'estratègia de l'usuari."""
        for id_partit, (g1_real, g2_real) in RESULTATS_GRUPS.items():
            try:
                partit = Partit.objects.get(pk=id_partit)
                pron, _ = PronosticPartit.objects.get_or_create(
                    jugador=jugador, partit=partit,
                    defaults={'equip1': partit.equip1, 'equip2': partit.equip2}
                )
                if index == 0:
                    # Perfecte: encerta tot
                    pron.gols1 = g1_real
                    pron.gols2 = g2_real
                elif index == 1:
                    # Signe: encerta signe però no resultat exacte
                    s = _signe(g1_real, g2_real)
                    if s == 1:
                        pron.gols1, pron.gols2 = g1_real + 1, g2_real
                    elif s == 2:
                        pron.gols1, pron.gols2 = g1_real, g2_real + 1
                    else:
                        pron.gols1, pron.gols2 = g1_real + 1, g2_real + 1
                elif index == 2:
                    # Mixt: encerta resultat exacte als parells, signe als senars
                    if id_partit % 2 == 0:
                        pron.gols1 = g1_real
                        pron.gols2 = g2_real
                    else:
                        s = _signe(g1_real, g2_real)
                        if s == 1:
                            pron.gols1, pron.gols2 = g1_real + 1, g2_real
                        elif s == 2:
                            pron.gols1, pron.gols2 = g1_real, g2_real + 1
                        else:
                            pron.gols1, pron.gols2 = g1_real + 1, g2_real + 1
                else:
                    # Dolent: signe contrari sempre
                    s = _signe(g1_real, g2_real)
                    if s == 1:
                        pron.gols1, pron.gols2 = 0, 1
                    elif s == 2:
                        pron.gols1, pron.gols2 = 1, 0
                    else:
                        pron.gols1, pron.gols2 = 1, 0
                pron.save()
            except Partit.DoesNotExist:
                pass

    def _classifica_grups(self, admin):
        """Classifica els grups per l'admin basant-se en els resultats reals."""
        for grup in Grup.objects.filter(nom__in=list('ABCDEFGHIJKL')):
            equips = list(Equip.objects.filter(grup=grup))
            # Calculem punts reals per classificar
            punts = {e.id: 0 for e in equips}
            gf = {e.id: 0 for e in equips}
            gc = {e.id: 0 for e in equips}
            for partit in Partit.objects.filter(grup=grup, gols1__gte=0):
                if partit.equip1 and partit.equip2:
                    g1, g2 = partit.gols1, partit.gols2
                    gf[partit.equip1_id] += g1
                    gc[partit.equip1_id] += g2
                    gf[partit.equip2_id] += g2
                    gc[partit.equip2_id] += g1
                    if g1 > g2:
                        punts[partit.equip1_id] += 3
                    elif g2 > g1:
                        punts[partit.equip2_id] += 3
                    else:
                        punts[partit.equip1_id] += 1
                        punts[partit.equip2_id] += 1

            classificats = sorted(
                equips,
                key=lambda e: (punts[e.id], gf[e.id] - gc[e.id], gf[e.id]),
                reverse=True
            )
            for pos, equip in enumerate(classificats, 1):
                peg, _ = PronosticEquipGrup.objects.get_or_create(
                    jugador=admin, equip=equip
                )
                peg.posicio = pos
                peg.punts = punts[equip.id]
                peg.diferencia = gf[equip.id] - gc[equip.id]
                peg.favor = gf[equip.id]
                peg.save()

    def _classifica_grups_usuari(self, jugador, index, admin):
        """Classifica els grups per l'usuari (amb encerts parcials)."""
        for grup in Grup.objects.filter(nom__in=list('ABCDEFGHIJKL')):
            equips = list(Equip.objects.filter(grup=grup))
            # Obtenim la classificació real (admin)
            admin_class = {
                peg.equip_id: peg.posicio
                for peg in PronosticEquipGrup.objects.filter(
                    jugador=admin, equip__grup=grup
                )
            }
            classificats = sorted(equips, key=lambda e: admin_class.get(e.id, 4))

            # Modifiquem segons l'estratègia
            if index == 0:
                # Perfecte: igual que l'admin
                ordre = classificats
            elif index == 1:
                # Encerta 2: invertim els dos últims
                ordre = classificats[:2] + list(reversed(classificats[2:]))
            elif index == 2:
                # Encerta 1: només encerta el primer
                ordre = [classificats[0]] + list(reversed(classificats[1:]))
            else:
                # Dolent: ordre invers
                ordre = list(reversed(classificats))

            for pos, equip in enumerate(ordre, 1):
                peg, _ = PronosticEquipGrup.objects.get_or_create(
                    jugador=jugador, equip=equip
                )
                peg.posicio = pos
                peg.save()
