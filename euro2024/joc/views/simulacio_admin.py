# -*- coding: utf-8 -*-
"""
Vista d'admin per executar la simulació de puntuació des del navegador.
Afegeix aquestes URLs al urls.py principal del projecte.
"""

from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from io import StringIO
import sys


@staff_member_required
def simulacio_view(request):
    """Vista per executar la simulació."""
    output = None
    error = None

    if request.method == 'POST':
        accio = request.POST.get('accio')

        # Capturem la sortida del command
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        try:
            if accio == 'simula':
                from django.core.management import call_command
                call_command('simula_pronostics')
            elif accio == 'esborra':
                from django.core.management import call_command
                call_command('esborra_simulacio')
            output = mystdout.getvalue()
        except Exception as e:
            error = str(e)
        finally:
            sys.stdout = old_stdout

    context = {
        'title': 'Simulació de Puntuació',
        'output': output,
        'error': error,
        'has_run': output is not None or error is not None,
    }
    return render(request, 'admin/simulacio.html', context)
