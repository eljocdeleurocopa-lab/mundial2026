# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.html import format_html

from django_registration.backends.activation.views import RegistrationView

from joc.models import (
    Jugador, Grup, Equip, Estadi, Partit,
    PronosticPartit, PronosticEquipGrup, PronosticEquipFase,
    FASE_SETZENS, FASE_VUITENS, FASE_QUARTS, FASE_SEMIS, FASE_TERCER, FASE_FINAL,
    FASE_CHOICES,
)


# =============================================================================
# JUGADOR
# =============================================================================

@admin.action(description='Acceptar els jugadors seleccionats')
def approve_players(modeladmin, request, queryset):
    rv = RegistrationView()
    rv.setup(request)
    for jugador in queryset:
        rv.send_activation_email(jugador.usuari)


@admin.action(description='Recalcular puntuacions dels jugadors seleccionats')
def recalcula_puntuacions(modeladmin, request, queryset):
    from joc.management.commands.calcula_puntuacions import (
        calcula_puntuacions_jugador, actualitza_ranking
    )
    for jugador in queryset:
        calcula_puntuacions_jugador(jugador)
    actualitza_ranking()
    modeladmin.message_user(request, f'Puntuacions recalculades per {queryset.count()} jugadors.')


@admin.action(description='Recalcular puntuacions de TOTS els jugadors')
def recalcula_totes_puntuacions(modeladmin, request, queryset):
    from joc.management.commands.calcula_puntuacions import (
        calcula_puntuacions_jugador, actualitza_ranking
    )
    from django.conf import settings
    tots = Jugador.objects.exclude(pk=settings.ID_ADMIN)
    for jugador in tots:
        calcula_puntuacions_jugador(jugador)
    actualitza_ranking()
    if request is not None:
        modeladmin.message_user(request, f'Puntuacions recalculades per {tots.count()} jugadors.')


class JugadorAdmin(admin.ModelAdmin):
    actions = [approve_players, recalcula_puntuacions, recalcula_totes_puntuacions]
    list_display = [
        'usuari', 'get_first_name', 'get_is_active', 'get_date_joined',
        'pagat', 'posicio', 'punts',
    ]
    list_filter  = ['usuari__is_active', 'pagat']
    ordering     = ['posicio']
    readonly_fields = [
        'punts', 'punts_anterior', 'posicio', 'posicio_anterior',
        'punts_resultats', 'punts_grups', 'punts_equips_encertats',
        'punts_setzens', 'punts_vuitens', 'punts_quarts',
        'punts_semis', 'punts_tercer', 'punts_final', 'punts_quadre_final',
    ]

    fieldsets = (
        ('Usuari', {
            'fields': ('usuari', 'pagat'),
        }),
        ('Rànquing', {
            'fields': ('posicio', 'posicio_anterior', 'punts', 'punts_anterior'),
        }),
        ('Desglossament de punts', {
            'fields': (
                'punts_resultats', 'punts_grups', 'punts_equips_encertats',
                'punts_setzens', 'punts_vuitens', 'punts_quarts',
                'punts_semis', 'punts_tercer', 'punts_final', 'punts_quadre_final',
            ),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Nom Real')
    def get_first_name(self, obj):
        return obj.usuari.first_name

    @admin.display(description='Data registre')
    def get_date_joined(self, obj):
        return obj.usuari.date_joined

    @admin.display(description='Activat?', boolean=True)
    def get_is_active(self, obj):
        return obj.usuari.is_active


admin.site.register(Jugador, JugadorAdmin)


# =============================================================================
# GRUP
# =============================================================================

class EquipInline(admin.TabularInline):
    model  = Equip
    extra  = 0
    fields = ['nom', 'bandera']


class GrupAdmin(admin.ModelAdmin):
    list_display = ['nom']
    ordering     = ['nom']
    inlines      = [EquipInline]


admin.site.register(Grup, GrupAdmin)


# =============================================================================
# EQUIP
# =============================================================================

class EquipAdmin(admin.ModelAdmin):
    list_display = ['nom', 'grup', 'get_bandera']
    list_filter  = ['grup']
    ordering     = ['grup__nom', 'nom']
    search_fields = ['nom']

    @admin.display(description='Bandera')
    def get_bandera(self, obj):
        if obj.bandera:
            return format_html(
                '<img src="{}" width="20" height="15" />',
                obj.bandera,
            )
        return '-'


admin.site.register(Equip, EquipAdmin)


# =============================================================================
# ESTADI
# =============================================================================

class EstadiAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ciutat']
    ordering     = ['ciutat']


admin.site.register(Estadi, EstadiAdmin)


# =============================================================================
# PARTIT
# =============================================================================

@admin.action(description='Ressetar gols i equips dels partits seleccionats')
def resseta_partits(modeladmin, request, queryset):
    """
    Resseta els gols i equips dels partits seleccionats.
    Útil per ressetar els partits eliminatoris després d'una simulació.
    """
    count = queryset.count()
    queryset.update(gols1=-1, gols2=-1, empat=None)
    # Esborrem també els PronosticPartit associats
    PronosticPartit.objects.filter(partit__in=queryset).delete()
    modeladmin.message_user(
        request,
        f'{count} partits ressetats (gols, equips i pronòstics eliminats).'
    )


@admin.action(description='Ressetar TOTS els partits eliminatoris (73-104)')
def resseta_tots_eliminatoris(modeladmin, request, queryset):
    """
    Resseta tots els partits eliminatoris independentment de la selecció.
    """
    partits = Partit.objects.filter(pk__gte=73)
    count = partits.count()
    PronosticPartit.objects.filter(partit__in=partits).delete()
    partits.update(gols1=-1, gols2=-1, empat=None)
    modeladmin.message_user(
        request,
        f'{count} partits eliminatoris ressetats completament.'
    )


class PartitAdmin(admin.ModelAdmin):
    actions = [recalcula_totes_puntuacions, resseta_partits, resseta_tots_eliminatoris]
    list_display  = [
        'id', 'grup', 'diaihora', 'equip1', 'get_resultat', 'equip2',
        'empat', 'estadi', 'get_jugat',
    ]
    list_filter   = ['grup']
    ordering      = ['id']
    search_fields = ['equip1__nom', 'equip2__nom']

    fields = [
        'grup', 'diaihora', 'estadi',
        'equip1', 'gols1',
        'equip2', 'gols2',
        'empat',
    ]

    @admin.display(description='Resultat')
    def get_resultat(self, obj):
        if obj.gols1 >= 0 and obj.gols2 >= 0:
            return f'{obj.gols1} - {obj.gols2}'
        return '- : -'

    @admin.display(description='Jugat?', boolean=True)
    def get_jugat(self, obj):
        return obj.gols1 >= 0 and obj.gols2 >= 0

    def get_list_display(self, request):
        return [
            'id', 'grup', 'diaihora', 'equip1', 'gols1',
            'get_guio', 'gols2', 'equip2', 'empat', 'get_jugat',
        ]

    @admin.display(description='-')
    def get_guio(self, obj):
        return '-'

    def save_model(self, request, obj, form, change):
        """En guardar un resultat real, recalcula els punts de tots els jugadors."""
        super().save_model(request, obj, form, change)
        if obj.gols1 >= 0 and obj.gols2 >= 0:
            recalcula_totes_puntuacions(self, request, queryset=None)


admin.site.register(Partit, PartitAdmin)


# =============================================================================
# PRONÒSTIC DE PARTIT (només lectura per a l'admin, útil per consultes)
# =============================================================================

class PronosticPartitAdmin(admin.ModelAdmin):
    list_display  = ['jugador', 'partit', 'equip1', 'gols1', 'gols2', 'equip2', 'empat']
    list_filter   = ['partit__grup', 'jugador']
    ordering      = ['partit__id', 'jugador']
    search_fields = ['jugador__usuari__username', 'equip1__nom', 'equip2__nom']
    raw_id_fields = ['jugador', 'partit', 'equip1', 'equip2']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


admin.site.register(PronosticPartit, PronosticPartitAdmin)


# =============================================================================
# PRONÒSTIC CLASSIFICACIÓ DE GRUP
# =============================================================================

class PronosticEquipGrupAdmin(admin.ModelAdmin):
    list_display  = ['jugador', 'equip', 'posicio', 'punts', 'diferencia', 'favor']
    list_filter   = ['equip__grup', 'jugador']
    ordering      = ['equip__grup__nom', 'posicio', 'jugador']
    search_fields = ['jugador__usuari__username', 'equip__nom']
    raw_id_fields = ['jugador', 'equip']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


admin.site.register(PronosticEquipGrup, PronosticEquipGrupAdmin)


# =============================================================================
# PRONÒSTIC EQUIPS CLASSIFICATS PER FASE
# =============================================================================

class PronosticEquipFaseAdmin(admin.ModelAdmin):
    list_display  = ['jugador', 'fase', 'equip', 'posicio']
    list_filter   = ['fase', 'jugador']
    ordering      = ['fase', 'posicio', 'jugador']
    search_fields = ['jugador__usuari__username', 'equip__nom']
    raw_id_fields = ['jugador', 'equip']

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


admin.site.register(PronosticEquipFase, PronosticEquipFaseAdmin)
