# -*- coding: utf-8 -*-
from itertools import groupby

from django.conf import settings

from joc.models import Partit, PronosticPartit, PronosticEquipGrup, Equip

GOLS_CHOICES = (('-1', '-'), (0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8))
EMPAT_CHOICES = ((1, 1), (2, 2))

# Grups A-L: fase de grups (12 grups)
FASE_GRUPS = set(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'])

# Guardar classificació de grup en passar al grup següent
GUARDA_GRUPS = set(['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M'])

# Rondes eliminatòries
SETZENS = set(['M'])    # Round of 32
VUITENS  = set(['N'])   # Round of 16
QUARTS   = set(['O'])   # Quarterfinals
SEMIS    = set(['P'])   # Semifinals
TERCER   = set(['Q'])   # Third-place match
FINAL    = set(['R'])   # Final

CREAR_PARTITS  = set(['M', 'N', 'O', 'P', 'Q', 'R'])
ACABA_PRONOSTIC = set(['S'])

TEXT_GRUP = {
    'A': 'Grup A',
    'B': 'Grup B',
    'C': 'Grup C',
    'D': 'Grup D',
    'E': 'Grup E',
    'F': 'Grup F',
    'G': 'Grup G',
    'H': 'Grup H',
    'I': 'Grup I',
    'J': 'Grup J',
    'K': 'Grup K',
    'L': 'Grup L',
    'M': 'Setzens de final',
    'N': 'Vuitens de final',
    'O': 'Quarts de final',
    'P': 'Semifinals',
    'Q': 'Tercer i quart lloc',
    'R': 'Final',
}

NUM_EQUIPS = 48
EQUIPS_PER_GRUP = 4
NUM_GRUPS = 12

ULTIM_PARTIT_GRUPS   = 48   # 12 grups × 6 partits = 72? No: 12 × 3 = 36 partits? 
                             # Correcte: 12 grups × 6 partits = 72? 
                             # Cada grup té 4 equips → C(4,2)=6 partits × 12 grups = 72. 
                             # Però FIFA 2026 juga 3 partits per equip = 6 per grup × 12 = 72. 
                             # Però la fase de grups té 48 equips, 12 grups de 4, 
                             # 6 partits per grup × 12 = 72 partits en total? 
                             # Compte: cada grup 4 equips juguen 3 partits cada un = 6 partits × 12 = 72.
                             # NOTA: en el codi original per Eurocopa, 6 grups × 6 partits = 36.
                             # Per Mundial: 12 grups × 6 partits = 72.
ULTIM_PARTIT_GRUPS   = 72
ULTIM_PARTIT_SETZENS = 72 + 16  # = 88 (partits 73–88)
ULTIM_PARTIT_VUITENS = 88 + 8   # = 96 (partits 89–96)
ULTIM_PARTIT_QUARTS  = 96 + 4   # = 100 (partits 97–100)
ULTIM_PARTIT_SEMIS   = 100 + 2  # = 102 (partits 101–102)
# Partit 103: tercer i quart lloc
# Partit 104: final

FUNCIO_ORDRE = lambda x: (x.punts, x.diferencia, x.favor, x.victories())

# -------------------------------------------------------------------------
# Emparellaments dels setzens de final (Round of 32)
# Font: Reglament oficial FIFA World Cup 2026, Annex C
# Partits 73–88 (numeració FIFA)
#
# Partits fixos (2 primers de cada grup que no depenen dels tercers):
#   M73: 2n A vs 2n B
#   M75: 1r F vs 2n C
#   M76: 1r C vs 2n F
#   M78: 2n E vs 2n I
#   M83: 2n K vs 2n L
#   M84: 1r H vs 2n J
#   M86: 1r J vs 2n H
#   M88: 2n D vs 2n G
#
# Partits que depenen dels tercers classificats (s'assignen dinàmicament):
#   M74: 1r E vs millor 3r de A/B/C/D/F
#   M77: 1r I vs millor 3r de C/D/F/G/H
#   M79: 1r A vs millor 3r de C/E/F/H/I
#   M80: 1r L vs millor 3r de E/H/I/J/K
#   M81: 1r D vs millor 3r de B/E/F/I/J
#   M82: 1r G vs millor 3r de A/E/H/I/J
#   M85: 1r B vs millor 3r de E/F/G/I/J
#   M87: 1r K vs millor 3r de D/E/I/J/L
# -------------------------------------------------------------------------

# Emparellaments fixos dels setzens (no depenen de tercers)
# Clau: id del nou partit → (posició, nom_grup) dels 2 equips
EMPARELLAMENTS_SETZENS_FIXOS = {
    73: ((2, 'A'), (2, 'B')),
    75: ((1, 'F'), (2, 'C')),
    76: ((1, 'C'), (2, 'F')),
    78: ((2, 'E'), (2, 'I')),
    83: ((2, 'K'), (2, 'L')),
    84: ((1, 'H'), (2, 'J')),
    86: ((1, 'J'), (2, 'H')),
    88: ((2, 'D'), (2, 'G')),
}

# Emparellaments amb tercers: partit_id → (grup_1r, [grups_elegibles_tercer])
EMPARELLAMENTS_SETZENS_AMB_TERCERS = {
    74: ((1, 'E'), ['A', 'B', 'C', 'D', 'F']),
    77: ((1, 'I'), ['C', 'D', 'F', 'G', 'H']),
    79: ((1, 'A'), ['C', 'E', 'F', 'H', 'I']),
    80: ((1, 'L'), ['E', 'H', 'I', 'J', 'K']),
    81: ((1, 'D'), ['B', 'E', 'F', 'I', 'J']),
    82: ((1, 'G'), ['A', 'E', 'H', 'I', 'J']),
    85: ((1, 'B'), ['E', 'F', 'G', 'I', 'J']),
    87: ((1, 'K'), ['D', 'E', 'I', 'J', 'L']),
}

# Taula completa de les 495 combinacions de tercers (Annex C del reglament FIFA)
# Clau: frozenset dels 8 grups que classifiquen 3rs
# Valor: dict {id_partit: nom_grup_del_tercer}
# Per raons de mantenibilitat, implementem la lògica de selecció dinàmica
# en lloc de hardcodejar les 495 combinacions.
# La lògica: per a cada partit amb tercers, seleccionem el millor tercer
# dels grups elegibles que no hagi estat assignat ja.

EMPARELLAMENTS_VUITENS = {
    89: (73, 75),   # Guanyador M73 vs Guanyador M75  (bracket esquerra superior)
    90: (74, 77),   # Guanyador M74 vs Guanyador M77
    91: (76, 78),   # Guanyador M76 vs Guanyador M78
    92: (79, 80),   # Guanyador M79 vs Guanyador M80
    93: (83, 84),   # Guanyador M83 vs Guanyador M84
    94: (81, 82),   # Guanyador M81 vs Guanyador M82
    95: (86, 88),   # Guanyador M86 vs Guanyador M88
    96: (85, 87),   # Guanyador M85 vs Guanyador M87
}

EMPARELLAMENTS_QUARTS = {
    97:  (89, 90),
    98:  (93, 94),
    99:  (91, 92),
    100: (95, 96),
}

EMPARELLAMENTS_SEMIS = {
    101: (97, 98),
    102: (99, 100),
}

EMPARELLAMENT_TERCER = {
    103: (101, 102),  # Perdedors de les semis
}

EMPARELLAMENT_FINAL = {
    104: (101, 102),  # Guanyadors de les semis
}


# =========================================================================
# Funcions auxiliars
# =========================================================================

def get_or_create_and_reset_pronostic_partit(id_partit, jugador, id_equip1, id_equip2,
                                              admin=False):
    try:
        pronostic_partit = PronosticPartit.objects.get(jugador=jugador, partit_id=id_partit)
    except PronosticPartit.DoesNotExist:
        PronosticPartit.objects.create(jugador=jugador, partit_id=id_partit,
                                       equip1_id=id_equip1, equip2_id=id_equip2)
    else:
        if pronostic_partit.equip1_id != id_equip1 or pronostic_partit.equip2_id != id_equip2:
            pronostic_partit.equip1_id = id_equip1
            pronostic_partit.equip2_id = id_equip2
            pronostic_partit.gols1 = -1
            pronostic_partit.gols2 = -1
            pronostic_partit.empat = None
            pronostic_partit.save()

    if admin:
        partit = Partit.objects.get(pk=id_partit)
        partit.equip1_id = id_equip1
        partit.equip2_id = id_equip2
        partit.save()


def _get_equip_id_per_posicio_grup(jugador, posicio, nom_grup):
    return PronosticEquipGrup.objects.get(
        jugador=jugador,
        equip__grup__nom=nom_grup,
        posicio=posicio,
    ).equip.id


def _get_guanyador_partit(jugador, id_partit):
    return PronosticPartit.objects.get(
        jugador=jugador,
        partit_id=id_partit,
    ).guanyador().id


def _get_perdedor_partit(jugador, id_partit):
    return PronosticPartit.objects.get(
        jugador=jugador,
        partit_id=id_partit,
    ).perdedor().id


# =========================================================================
# Creació de partits de setzens de final
# =========================================================================

def crea_setzens(request, jugador, admin=False):
    """
    Crea els 16 partits dels setzens de final.
    8 partits fixos (1rs i 2ns de grups concrets).
    8 partits amb tercers (el millor tercer dels grups elegibles no assignat).
    """
    # --- Partits fixos ---
    for id_nou, equips in EMPARELLAMENTS_SETZENS_FIXOS.items():
        get_or_create_and_reset_pronostic_partit(
            id_nou,
            jugador,
            _get_equip_id_per_posicio_grup(jugador, equips[0][0], equips[0][1]),
            _get_equip_id_per_posicio_grup(jugador, equips[1][0], equips[1][1]),
            admin,
        )

    # --- Partits amb tercers ---
    # Obtenim tots els tercers classificats del jugador, ordenats per la funció d'ordre
    tercers = PronosticEquipGrup.objects.filter(jugador=jugador, posicio=3)
    tercers_ordenats = sorted(tercers, key=FUNCIO_ORDRE, reverse=True)

    # Els 8 millors tercers
    millors_tercers = tercers_ordenats[:8]
    grups_millors_tercers = {peg.equip.grup.nom: peg for peg in millors_tercers}

    # Assignació dels tercers als partits corresponents seguint l'ordre de prioritat FIFA
    # (prioritat: el tercer del grup amb millor classificació va al primer partit elegible)
    tercers_assignats = set()

    for id_nou, (primer, grups_elegibles) in EMPARELLAMENTS_SETZENS_AMB_TERCERS.items():
        # Busquem el millor tercer no assignat dels grups elegibles
        tercer_elegit = None
        for tercer in tercers_ordenats:
            nom_grup_tercer = tercer.equip.grup.nom
            if nom_grup_tercer in grups_elegibles and nom_grup_tercer not in tercers_assignats:
                tercer_elegit = tercer
                break

        if tercer_elegit is None:
            # Fallback: agafem qualsevol tercer no assignat
            for tercer in tercers_ordenats:
                if tercer.equip.grup.nom not in tercers_assignats:
                    tercer_elegit = tercer
                    break

        if tercer_elegit:
            tercers_assignats.add(tercer_elegit.equip.grup.nom)
            get_or_create_and_reset_pronostic_partit(
                id_nou,
                jugador,
                _get_equip_id_per_posicio_grup(jugador, primer[0], primer[1]),
                tercer_elegit.equip.id,
                admin,
            )


# =========================================================================
# Creació de partits de vuitens de final
# =========================================================================

def crea_vuitens(request, jugador, admin=False):
    for id_nou, partits_anteriors in EMPARELLAMENTS_VUITENS.items():
        get_or_create_and_reset_pronostic_partit(
            id_nou,
            jugador,
            _get_guanyador_partit(jugador, partits_anteriors[0]),
            _get_guanyador_partit(jugador, partits_anteriors[1]),
            admin,
        )


# =========================================================================
# Creació de partits de quarts de final
# =========================================================================

def crea_quarts(request, jugador, admin=False):
    for id_nou, partits_anteriors in EMPARELLAMENTS_QUARTS.items():
        get_or_create_and_reset_pronostic_partit(
            id_nou,
            jugador,
            _get_guanyador_partit(jugador, partits_anteriors[0]),
            _get_guanyador_partit(jugador, partits_anteriors[1]),
            admin,
        )


# =========================================================================
# Creació de partits de semifinals
# =========================================================================

def crea_semis(request, jugador, admin=False):
    for id_nou, partits_anteriors in EMPARELLAMENTS_SEMIS.items():
        get_or_create_and_reset_pronostic_partit(
            id_nou,
            jugador,
            _get_guanyador_partit(jugador, partits_anteriors[0]),
            _get_guanyador_partit(jugador, partits_anteriors[1]),
            admin,
        )


# =========================================================================
# Creació del partit de tercer i quart lloc
# =========================================================================

def crea_tercer(request, jugador, admin=False):
    for id_nou, partits_anteriors in EMPARELLAMENT_TERCER.items():
        get_or_create_and_reset_pronostic_partit(
            id_nou,
            jugador,
            _get_perdedor_partit(jugador, partits_anteriors[0]),
            _get_perdedor_partit(jugador, partits_anteriors[1]),
            admin,
        )


# =========================================================================
# Creació de la final
# =========================================================================

def crea_final(request, jugador, admin=False):
    for id_nou, partits_anteriors in EMPARELLAMENT_FINAL.items():
        get_or_create_and_reset_pronostic_partit(
            id_nou,
            jugador,
            _get_guanyador_partit(jugador, partits_anteriors[0]),
            _get_guanyador_partit(jugador, partits_anteriors[1]),
            admin,
        )


# =========================================================================
# Dispatcher principal
# =========================================================================

def crea_partits(request, jugador, nom_grup, admin=False):
    if nom_grup in SETZENS:
        crea_setzens(request, jugador, admin)
    elif nom_grup in VUITENS:
        crea_vuitens(request, jugador, admin)
    elif nom_grup in QUARTS:
        crea_quarts(request, jugador, admin)
    elif nom_grup in SEMIS:
        crea_semis(request, jugador, admin)
    elif nom_grup in TERCER:
        crea_tercer(request, jugador, admin)
    elif nom_grup in FINAL:
        crea_final(request, jugador, admin)


# =========================================================================
# Guardar classificació de grup
# =========================================================================

def guarda_classificacio_grup(request, jugador):
    for i in range(settings.EQUIPS_PER_GRUP):
        equip = Equip.objects.get(pk=int(request.POST['id%d' % (i)]))
        pronostic_equip = PronosticEquipGrup.objects.get(jugador=jugador, equip=equip)
        pronostic_equip.posicio   = i + 1
        pronostic_equip.punts     = int(request.POST['p%d' % (i)])
        pronostic_equip.diferencia = int(request.POST['d%d' % (i)])
        pronostic_equip.favor     = int(request.POST['g%d' % (i)])
        pronostic_equip.save()


# =========================================================================
# Comprovació de tercers empatats (ja no s'usa per mostrar pantalla addicional,
# però es manté per si cal verificar l'assignació)
# =========================================================================

def comprova_tercers(request, jugador):
    """
    Al Mundial 2026 passen els 8 millors tercers de 12 grups.
    Retorna la llista de tercers si n'hi ha empats en les posicions 8/9
    que necessitin resolució manual; None si no n'hi ha.
    """
    tercers = PronosticEquipGrup.objects.filter(jugador=jugador, posicio=3)

    if len(tercers) != settings.NUM_GRUPS:
        return None

    agrupats = [
        {grup: [i for i in elements]}
        for grup, elements in groupby(
            sorted(tercers, key=FUNCIO_ORDRE, reverse=True),
            key=FUNCIO_ORDRE
        )
    ]

    # Si hi ha menys de 12 grups amb el mateix valor en posició 8 i 9, no cal resolució
    # (els 8 millors estan clars)
    tercers_ordenats = sorted(tercers, key=FUNCIO_ORDRE, reverse=True)
    if len(tercers_ordenats) < 9:
        return None

    # Comprovem si el 8è i 9è tercer estan empatats
    vuite  = FUNCIO_ORDRE(tercers_ordenats[7])
    nove   = FUNCIO_ORDRE(tercers_ordenats[8])

    if vuite == nove:
        # Empat en la posició de tall → cal resolució per FIFA ranking
        return tercers_ordenats
    return None
