# -*- coding: utf-8 -*-
import os
from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views
from .views.usuaris import UsuarisView
from .views.consulta import ConsultaView
from .views.classificacio import ClassificacioView

app_name = 'joc'

# FASE_MUNDIAL controla quines URLs estan actives:
#   'pronostics' → abans de l'11 de juny (per defecte)
#   'mundial'    → el Mundial ha començat
FASE_MUNDIAL = os.getenv('FASE_MUNDIAL', 'pronostics')

urlpatterns = [
    # Sempre disponibles
    path('', views.index, name='index'),
    path('consulta_grups', views.consulta_grups, name='consulta_grups'),
    path('consulta', login_required(ConsultaView.as_view()), name='consulta'),
    path('usuaris', login_required(UsuarisView.as_view()), name='usuaris'),
    path('puntuacions', views.puntuacions, name='puntuacions'),
]

# /pronostic sempre disponible — la vista controla qui hi pot accedir
urlpatterns += [
    path('pronostic', views.pronostic, name='pronostic'),
]

if FASE_MUNDIAL != 'pronostics':
    # Durant el Mundial, afegim la classificació
    urlpatterns += [
        path('classificacio', login_required(ClassificacioView.as_view()), name='classificacio'),
    ]
