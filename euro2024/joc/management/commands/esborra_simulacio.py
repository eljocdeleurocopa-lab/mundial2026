# -*- coding: utf-8 -*-
"""
Management command per esborrar les dades de simulació.

Ús:
    python manage.py esborra_simulacio
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

from joc.models import (
    Jugador, Partit, PronosticPartit, PronosticEquipGrup, PronosticEquipFase,
)


class Command(BaseCommand):
    help = 'Esborra les dades de simulació (resultats fictícis i pronòstics de prova)'

    def handle(self, *args, **options):
        self.stdout.write('Esborrant dades de simulació...')

        # Esborrem resultats reals dels partits
        Partit.objects.all().update(gols1=-1, gols2=-1, empat=None)
        self.stdout.write('✓ Resultats dels partits esborrats')

        # Esborrem pronòstics dels usuaris de prova
        usuaris = ['prova1', 'prova2', 'prova3', 'prova4']
        for nom in usuaris:
            try:
                user = User.objects.get(username=nom)
                jugador = Jugador.objects.get(usuari=user)
                PronosticPartit.objects.filter(jugador=jugador).delete()
                PronosticEquipGrup.objects.filter(jugador=jugador).delete()
                PronosticEquipFase.objects.filter(jugador=jugador).delete()
                jugador.punts = 0
                jugador.punts_anterior = 0
                jugador.punts_resultats = 0
                jugador.punts_grups = 0
                jugador.punts_equips_encertats = 0
                jugador.punts_setzens = 0
                jugador.punts_vuitens = 0
                jugador.punts_quarts = 0
                jugador.punts_semis = 0
                jugador.punts_tercer = 0
                jugador.punts_final = 0
                jugador.punts_quadre_final = 0
                jugador.save()
                self.stdout.write(f'✓ Pronòstics de {nom} esborrats')
            except (User.DoesNotExist, Jugador.DoesNotExist):
                self.stdout.write(f'  - {nom} no trobat, saltant')

        # Esborrem pronòstics de l'admin
        try:
            admin = Jugador.objects.get(pk=settings.ID_ADMIN)
            PronosticEquipGrup.objects.filter(jugador=admin).delete()
            PronosticEquipFase.objects.filter(jugador=admin).delete()
            self.stdout.write('✓ Pronòstics admin esborrats')
        except Jugador.DoesNotExist:
            pass

        self.stdout.write('✓ Simulació esborrada correctament')
