from django.db import models
from django.db.models import Q, F
from django.contrib.auth.models import User

from django_registration.signals import user_registered


# =============================================================================
# JUGADOR
# =============================================================================

class Jugador(models.Model):
    usuari           = models.OneToOneField(User, on_delete=models.CASCADE)
    pagat            = models.BooleanField(default=False)
    posicio          = models.SmallIntegerField()
    posicio_anterior = models.SmallIntegerField()

    # Puntuació total i anterior (per mostrar moviment al rànquing)
    punts          = models.SmallIntegerField(default=0)
    punts_anterior = models.SmallIntegerField(default=0)

    # Desglossament de punts per categoria
    punts_resultats        = models.PositiveSmallIntegerField(default=0)  # partits fase grups
    punts_grups            = models.PositiveSmallIntegerField(default=0)  # classificació grups
    punts_equips_encertats = models.PositiveSmallIntegerField(default=0)  # equips classificats rondes
    punts_setzens          = models.PositiveSmallIntegerField(default=0)  # partits setzens
    punts_vuitens          = models.PositiveSmallIntegerField(default=0)  # partits vuitens
    punts_quarts           = models.PositiveSmallIntegerField(default=0)  # partits quarts
    punts_semis            = models.PositiveSmallIntegerField(default=0)  # partits semis
    punts_tercer           = models.PositiveSmallIntegerField(default=0)  # partit 3r/4t lloc
    punts_final            = models.PositiveSmallIntegerField(default=0)  # partit final
    punts_quadre_final     = models.PositiveSmallIntegerField(default=0)  # campió/subcampió/3r/4t

    def __str__(self):
        return self.usuari.username

    @property
    def pronostic_acabat(self):
        """
        El pronòstic es considera acabat quan el jugador ha introduït
        el pronòstic de l'últim partit de la fase de grups (partit 72).
        """
        from django.conf import settings
        return PronosticPartit.objects.filter(
            jugador=self,
            partit_id=settings.NUM_PARTITS
        ).exists()


# =============================================================================
# GRUP
# =============================================================================

class Grup(models.Model):
    nom = models.CharField(max_length=32)  # 'A'..'L' per grups, 'M'..'R' per rondes

    def __str__(self):
        return self.nom


# =============================================================================
# EQUIP
# =============================================================================

class Equip(models.Model):
    nom     = models.CharField(max_length=128)
    bandera = models.CharField(max_length=128)
    grup    = models.ForeignKey(Grup, on_delete=models.CASCADE)

    def __str__(self):
        return self.nom


# =============================================================================
# PRONÒSTIC CLASSIFICACIÓ DE GRUP
# =============================================================================

class PronosticEquipGrup(models.Model):
    """
    Pronòstic de l'ordre de classificació dins un grup de la fase de grups.
    posicio: 1=primer, 2=segon, 3=tercer, 4=quart
    """
    jugador    = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    equip      = models.ForeignKey(Equip, on_delete=models.CASCADE)
    posicio    = models.PositiveSmallIntegerField(default=0)
    punts      = models.PositiveSmallIntegerField(default=0)
    diferencia = models.SmallIntegerField(default=0)
    favor      = models.PositiveSmallIntegerField(default=0)

    def victories(self):
        """Victòries pronostificades a la fase de grups (partits 1-72)."""
        return PronosticPartit.objects.filter(
            Q(jugador=self.jugador)
            & Q(partit_id__lte=72)   # Mundial 2026: 72 partits de fase de grups
            & (
                (Q(equip1=self.equip) & Q(gols1__gt=F('gols2')))
                | (Q(equip2=self.equip) & Q(gols2__gt=F('gols1')))
            )
        ).count()


# =============================================================================
# PRONÒSTIC D'EQUIPS CLASSIFICATS PER RONDA ELIMINATÒRIA
# =============================================================================

# Codis de fase per a PronosticEquipFase
FASE_SETZENS = 'R32'   # Round of 32  — 32 equips
FASE_VUITENS = 'R16'   # Round of 16  — 16 equips
FASE_QUARTS  = 'QF'    # Quarterfinals —  8 equips
FASE_SEMIS   = 'SF'    # Semifinals   —  4 equips
FASE_TERCER  = '3rd'   # Tercer lloc  —  (posicions 3 i 4)
FASE_FINAL   = 'F'     # Final        —  (posicions 1 i 2)

FASE_CHOICES = [
    (FASE_SETZENS, 'Setzens de final'),
    (FASE_VUITENS, 'Vuitens de final'),
    (FASE_QUARTS,  'Quarts de final'),
    (FASE_SEMIS,   'Semifinals'),
    (FASE_TERCER,  'Tercer i quart lloc'),
    (FASE_FINAL,   'Final'),
]


class PronosticEquipFase(models.Model):
    """
    Pronòstic de quins equips arriben a cada ronda eliminatòria.

    Per a les fases R32, R16, QF, SF: només cal saber si l'equip hi arriba
    (un registre per equip pronosticat = l'equip passa a aquella ronda).

    Per a 3rd i F: el camp `posicio` indica la posició pronosticada:
        Final:         1 = campió, 2 = subcampió
        Tercer/quart:  3 = tercer, 4 = quart
    """
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    fase    = models.CharField(max_length=3, choices=FASE_CHOICES)
    equip   = models.ForeignKey(Equip, on_delete=models.CASCADE)
    posicio = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('jugador', 'fase', 'equip')

    def __str__(self):
        return f'{self.jugador} - {self.fase} - {self.equip}'


# =============================================================================
# ESTADI
# =============================================================================

class Estadi(models.Model):
    nom    = models.CharField(max_length=128)
    ciutat = models.CharField(max_length=128)

    def __str__(self):
        return f'{self.nom} ({self.ciutat})'


# =============================================================================
# PARTIT (resultat real)
# =============================================================================

class Partit(models.Model):
    equip1    = models.ForeignKey(Equip, related_name='equip1', null=True, on_delete=models.CASCADE)
    equip2    = models.ForeignKey(Equip, related_name='equip2', null=True, on_delete=models.CASCADE)
    diaihora  = models.DateTimeField()
    estadi    = models.ForeignKey(Estadi, on_delete=models.CASCADE)
    grup      = models.ForeignKey(Grup, on_delete=models.CASCADE)
    gols1     = models.SmallIntegerField(default=-1)
    gols2     = models.SmallIntegerField(default=-1)
    # empat: en rondes eliminatòries, quin equip guanya per penals/pròrroga
    # 1 = guanya equip1, 2 = guanya equip2
    empat     = models.PositiveSmallIntegerField(null=True, blank=True, default=None)

    def signe(self):
        """Signe del resultat als 90 minuts (1=local, 2=visitant, 0=empat)."""
        if self.gols1 > self.gols2:
            return 1
        elif self.gols2 > self.gols1:
            return 2
        else:
            return 0

    def __str__(self):
        return '[{pk} - {grup}] {equip1} - {equip2}'.format(
            pk=self.pk,
            grup=self.grup,
            equip1=self.equip1,
            equip2=self.equip2,
        )

    def resultat_encertat(self, pronostic):
        return (self.gols1 == pronostic.gols1 and self.gols2 == pronostic.gols2)

    def signe_encertat(self, pronostic):
        return self.signe() == pronostic.signe()

    def guanyador(self):
        if self.gols1 > self.gols2:
            return self.equip1
        elif self.gols2 > self.gols1:
            return self.equip2
        elif self.empat == 1:
            return self.equip1
        else:
            return self.equip2

    def perdedor(self):
        if self.gols1 > self.gols2:
            return self.equip2
        elif self.gols2 > self.gols1:
            return self.equip1
        elif self.empat == 1:
            return self.equip2
        else:
            return self.equip1


# =============================================================================
# PRONÒSTIC DE PARTIT
# =============================================================================

class PronosticPartit(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    partit  = models.ForeignKey(Partit, on_delete=models.CASCADE)
    gols1   = models.SmallIntegerField(default=-1)
    gols2   = models.SmallIntegerField(default=-1)
    equip1  = models.ForeignKey(
        Equip, related_name='equip1_pronostic', null=True, on_delete=models.CASCADE)
    equip2  = models.ForeignKey(
        Equip, related_name='equip2_pronostic', null=True, on_delete=models.CASCADE)
    # empat: en rondes eliminatòries, quin equip guanya
    # 1 = guanya equip1, 2 = guanya equip2
    empat   = models.PositiveSmallIntegerField(null=True, blank=True, default=None)

    class Meta:
        unique_together = ('jugador', 'partit')

    def signe(self):
        """Signe del pronòstic als 90 minuts."""
        if self.gols1 > self.gols2:
            return 1
        elif self.gols2 > self.gols1:
            return 2
        else:
            return 0

    def guanyador(self):
        if self.gols1 > self.gols2:
            return self.equip1 or self.partit.equip1
        elif self.gols2 > self.gols1:
            return self.equip2 or self.partit.equip2
        elif self.empat == 1:
            return self.equip1 or self.partit.equip1
        else:
            return self.equip2 or self.partit.equip2

    def perdedor(self):
        if self.gols1 > self.gols2:
            return self.equip2 or self.partit.equip2
        elif self.gols2 > self.gols1:
            return self.equip1 or self.partit.equip1
        elif self.empat == 1:
            return self.equip2 or self.partit.equip2
        else:
            return self.equip1 or self.partit.equip1

    def __str__(self):
        return f'{self.jugador} - Partit {self.partit_id}'


# =============================================================================
# REGISTRE D'USUARI
# =============================================================================

def user_registered_callback(sender, user, request, **kwargs):
    Jugador.objects.create(
        usuari=user,
        posicio=user.id,
        posicio_anterior=user.id,
    )
    # Notificació a l'admin quan es registra un nou jugador
    from django.core.mail import send_mail
    from django.conf import settings as django_settings
    send_mail(
        subject=f'Nou jugador registrat: {user.username}',
        message=(
            f"S'ha registrat un nou jugador al Joc del Mundial 2026:\n\n"
            f"Nom d'usuari: {user.username}\n"
            f"Nom real: {user.first_name} {user.last_name}\n"
            f"Correu: {user.email}\n\n"
            f"Recorda assignar-li la lliga des de l'administrador."
        ),
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        recipient_list=['eljocdelmundial@gmail.com'],
        fail_silently=True,
    )

user_registered.connect(user_registered_callback)
