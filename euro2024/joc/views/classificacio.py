from datetime import timedelta
from django.conf import settings
from django.db.models import Q, F
from django.views import generic

from joc.models import Jugador, Partit


class ClassificacioView(generic.ListView):
    template_name = "joc/classificacio.html"

    def get_queryset(self):
        try:
            jugador_actual = Jugador.objects.get(usuari=self.request.user)
            lliga = jugador_actual.lliga
        except Jugador.DoesNotExist:
            lliga = ''

        return Jugador.objects.filter(
            usuari__is_active=True,
            lliga=lliga,
        ).filter(~Q(usuari_id=settings.ID_ADMIN)).annotate(
            dif_pos=F('posicio_anterior') - F('posicio')).annotate(
            dif_punts=F('punts') - F('punts_anterior')).order_by('posicio')

    def get_context_data(self, **kwargs):
        context = super(ClassificacioView, self).get_context_data(**kwargs)
        try:
            ultim_partit = Partit.objects.filter(~Q(gols1=-1)).order_by('-diaihora')[0]
            context['ultima_actualitzacio'] = ultim_partit.diaihora + timedelta(minutes=105)
        except IndexError:
            context['ultima_actualitzacio'] = None
        return context
