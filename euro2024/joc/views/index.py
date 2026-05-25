from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from joc.models import Jugador, PronosticEquipGrup
from joc.utils import NUM_EQUIPS

@login_required
def index(request):
    jugador, _ = Jugador.objects.get_or_create(
        usuari=request.user,
        defaults={'posicio': 0, 'posicio_anterior': 0},
    )
    pronostic_acabat = PronosticEquipGrup.objects.filter(
        jugador=jugador, posicio__gt=0).count() == NUM_EQUIPS

    fase_mundial = getattr(settings, 'FASE_MUNDIAL', 'pronostics')

    return render(
        request,
        'joc/index.html',
        {
            'jugador': jugador,
            'pronostic_acabat': pronostic_acabat,
            'fase_mundial': fase_mundial,
        }
    )
