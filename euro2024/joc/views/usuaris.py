from django.db.models import Q
from django.conf import settings
from django.views import generic

from joc.models import Jugador


class UsuarisView(generic.ListView):
    def get_queryset(self):
        try:
            jugador_actual = Jugador.objects.get(usuari=self.request.user)
            lliga = jugador_actual.lliga
        except Jugador.DoesNotExist:
            lliga = ''

        return Jugador.objects.filter(
            usuari__is_active=True,
            lliga=lliga,
        ).filter(~Q(usuari_id=settings.ID_ADMIN))
