# -*- coding: utf-8 -*-
from django.views import generic
from django.db.models import Q

from joc.models import PronosticPartit


class ConsultaView(generic.ListView):
    template_name = 'joc/consulta.html'
    context_object_name = 'pronostics'

    def get_queryset(self):
        usuari_id = self.request.GET.get('usuari')
        if usuari_id:
            return PronosticPartit.objects.filter(
                jugador_id=usuari_id
            ).order_by('partit__diaihora')
        else:
            return PronosticPartit.objects.filter(
                jugador__usuari=self.request.user
            ).order_by('partit__diaihora')
