# -*- coding: utf-8 -*-
from django.views import generic
from django.db.models import Q

from joc.models import PronosticPartit, Partit


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Nom de l'usuari consultat
        usuari_id = self.request.GET.get('usuari')
        if usuari_id:
            from joc.models import Jugador
            try:
                jugador = Jugador.objects.get(pk=usuari_id)
                context['nom_usuari'] = jugador.usuari.username
            except Jugador.DoesNotExist:
                context['nom_usuari'] = None
        else:
            context['nom_usuari'] = None

        # Últim partit amb resultat real
        try:
            ultim_partit = Partit.objects.filter(
                gols1__gte=0, gols2__gte=0
            ).order_by('-diaihora').first()
            context['ultim_partit_id'] = ultim_partit.id if ultim_partit else None
        except Exception:
            context['ultim_partit_id'] = None

        return context
