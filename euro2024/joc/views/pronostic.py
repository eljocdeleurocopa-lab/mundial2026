# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django import forms
from django.shortcuts import redirect, render

from joc.models import (
    Grup, Jugador, Equip, Partit, PronosticPartit, PronosticEquipGrup, PronosticEquipFase,
    FASE_SETZENS, FASE_VUITENS, FASE_QUARTS, FASE_SEMIS, FASE_TERCER, FASE_FINAL,
)
from joc.utils import (
    GOLS_CHOICES, EMPAT_CHOICES,
    GUARDA_GRUPS, FASE_GRUPS, ACABA_PRONOSTIC,
    SETZENS, VUITENS, QUARTS, SEMIS, TERCER, FINAL,
    TEXT_GRUP, crea_partits, comprova_tercers, guarda_classificacio_grup, CREAR_PARTITS,
    pronostics_oberts,
)


# =============================================================================
# FORMULARIS
# =============================================================================

class PartitForm(forms.ModelForm):
    gols1 = forms.ChoiceField(
        choices=GOLS_CHOICES,
        widget=forms.Select(attrs={"onChange": 'actualitza_grups()'}),
    )
    gols2 = forms.ChoiceField(
        choices=GOLS_CHOICES,
        widget=forms.Select(attrs={"onChange": 'actualitza_grups()'}),
    )
    empat = forms.ChoiceField(
        choices=EMPAT_CHOICES,
        widget=forms.RadioSelect,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(PartitForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk and (
            (instance.gols1 == -1 and instance.gols2 == -1)
            or (instance.gols1 != -1 and instance.gols1 != instance.gols2)
        ):
            self.fields['empat'].widget.attrs['disabled'] = True

        if instance and instance.partit and instance.partit.grup.nom in FASE_GRUPS:
            self.fields['gols1'].widget.attrs['onChange'] = 'actualitza_grups()'
            self.fields['gols2'].widget.attrs['onChange'] = 'actualitza_grups()'
        else:
            self.fields['gols1'].widget.attrs['onChange'] = 'actualitza_eliminatoria()'
            self.fields['gols2'].widget.attrs['onChange'] = 'actualitza_eliminatoria()'
            self.fields['empat'].widget.attrs['onChange'] = 'actualitza_eliminatoria()'

    class Meta:
        model = PronosticPartit
        fields = ('gols1', 'gols2', 'empat')


GrupForm = forms.modelformset_factory(PronosticPartit, form=PartitForm, extra=0)


# =============================================================================
# VISTA PRINCIPAL DE PRONÒSTIC
# =============================================================================

@login_required
def pronostic(request):
    from django.conf import settings as django_settings
    jugador = Jugador.objects.get(usuari=request.user)
    nom_grup = request.GET.get('grup', 'A')

    # Flanders (admin) sempre pot accedir a /pronostic
    # Els altres jugadors només si els pronòstics estan oberts
    es_admin = (jugador.id == django_settings.ID_ADMIN)
    if not pronostics_oberts() and not es_admin:
        return redirect('/')

    # --- POST: guardem els valors del formulari ---
    if request.method == 'POST':
        grup_form = GrupForm(request.POST)
        if grup_form.is_valid():
            grup_form.save()
        else:
            pass

        # El grup actual (d'on venim) és el camp POST 'nom-grup'
        # nom_grup (GET) és el grup destí (on anem)
        grup_actual = request.POST.get('nom-grup', nom_grup)

        # Guardem classificació d'equips del grup anterior
        if nom_grup in GUARDA_GRUPS:
            guarda_classificacio_grup(request, jugador)

        # Guardem pronòstics d'equips classificats (rondes eliminatòries)
        if grup_actual in SETZENS:
            _guarda_equips_fase_participants(request, jugador, FASE_SETZENS, 32)
            _guarda_equips_fase(request, jugador, FASE_VUITENS, 16)
        elif grup_actual in VUITENS:
            _guarda_equips_fase_participants(request, jugador, FASE_VUITENS, 16)
            _guarda_equips_fase(request, jugador, FASE_QUARTS, 8)
        elif grup_actual in QUARTS:
            _guarda_equips_fase_participants(request, jugador, FASE_QUARTS, 8)
            _guarda_equips_fase(request, jugador, FASE_SEMIS, 4)
        elif grup_actual in SEMIS:
            _guarda_equips_fase_participants(request, jugador, FASE_SEMIS, 4)
        elif grup_actual in TERCER:
            _guarda_equips_posicio_fase(request, jugador, FASE_TERCER, [3, 4])
        elif grup_actual in FINAL:
            _guarda_equips_posicio_fase(request, jugador, FASE_FINAL, [1, 2])

        # Creem els partits de la nova ronda si cal
        if nom_grup in CREAR_PARTITS:
            crea_partits(request, jugador, nom_grup)

        # Comprovem si hi ha tercers empatats (posició 8/9) — al final de la fase de grups
        # nom_grup='M' vol dir que acabem de passar l'últim grup (L) i anem als setzens
        if nom_grup in SETZENS:
            tercers_empatats = comprova_tercers(request, jugador)
            if tercers_empatats:
                grup = Grup.objects.get(nom='L')
                grup_form_actual = GrupForm(
                    queryset=PronosticPartit.objects.filter(
                        jugador=jugador, partit__grup=grup
                    )
                )
                return render(
                    request,
                    'joc/tercers.html',
                    {
                        'formset': grup_form_actual,
                        'jugador': jugador,
                        'tercers': tercers_empatats,
                        'text_grup': 'Tercers empatats',
                        'grup': 'L',
                        'height_banderes': 19,
                        'width_banderes': 19,
                        'border_banderes': 1,
                    }
                )

        if nom_grup in ACABA_PRONOSTIC:
            return redirect('/')

    # --- GET: mostrem el formulari ---
    grup = Grup.objects.get(nom=nom_grup)

    # Si és una ronda eliminatòria (no setzens), recalculem els partits
    if nom_grup in CREAR_PARTITS and nom_grup not in SETZENS:
        try:
            crea_partits(request, jugador, nom_grup)
        except Exception:
            pass

    try:
        seguent_grup = Grup.objects.get(id=grup.id + 1).nom
    except Grup.DoesNotExist:
        seguent_grup = 'S'

    partits = Partit.objects.filter(grup=grup).order_by("diaihora")

    for partit in partits:
        items = {}
        if nom_grup in FASE_GRUPS:
            items['equip1'] = partit.equip1
            items['equip2'] = partit.equip2
        PronosticPartit.objects.get_or_create(jugador=jugador, partit=partit, **items)

    grup_form = GrupForm(
        queryset=PronosticPartit.objects.filter(
            jugador=jugador, partit__grup=grup
        ).order_by("partit__diaihora")
    )

    equips_classificacio = []
    deshabilita_submit = False

    if nom_grup in FASE_GRUPS:
        tots_amb_posicio = True
        for equip in Equip.objects.filter(grup=grup):
            equip_classificacio, _ = PronosticEquipGrup.objects.get_or_create(
                jugador=jugador, equip=equip
            )
            equips_classificacio.append(equip_classificacio)
            if equip_classificacio.posicio == 0:
                tots_amb_posicio = False

        tots_partits_ok = True
        for form in grup_form.forms:
            inst = form.instance
            if inst.gols1 == -1 or inst.gols2 == -1:
                tots_partits_ok = False
                break
            elif inst.gols1 == inst.gols2 and not inst.empat:
                tots_partits_ok = False
                break

        deshabilita_submit = not (tots_amb_posicio and tots_partits_ok)
    else:
        for form in grup_form.forms:
            inst = form.instance
            if inst.gols1 == -1 or inst.gols2 == -1:
                deshabilita_submit = True
                break
            elif inst.gols1 == inst.gols2 and not inst.empat:
                deshabilita_submit = True
                break

    response = render(
        request,
        'joc/grup.html',
        {
            'formset': grup_form,
            'equips_classificacio': sorted(equips_classificacio, key=lambda k: k.posicio),
            'height_banderes': 19,
            'width_banderes': 19,
            'border_banderes': 0,
            'grup': grup.nom,
            'seguent_grup': seguent_grup,
            'deshabilita_submit': deshabilita_submit,
            'text_grup': TEXT_GRUP[nom_grup],
        }
    )

    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response


# =============================================================================
# FUNCIONS AUXILIARS DE GUARDAT D'EQUIPS CLASSIFICATS
# =============================================================================

def _guarda_equips_fase(request, jugador, fase, num_equips):
    PronosticEquipFase.objects.filter(jugador=jugador, fase=fase).delete()
    for i in range(num_equips):
        equip_id = request.POST.get(f'equip_{i}')
        if equip_id:
            try:
                equip = Equip.objects.get(pk=int(equip_id))
                PronosticEquipFase.objects.get_or_create(
                    jugador=jugador,
                    fase=fase,
                    equip=equip,
                    defaults={'posicio': 0},
                )
            except (Equip.DoesNotExist, ValueError):
                pass


def _guarda_equips_fase_participants(request, jugador, fase, num_equips):
    PronosticEquipFase.objects.filter(jugador=jugador, fase=fase).delete()
    for i in range(num_equips):
        equip_id = request.POST.get(f'participant_{i}')
        if equip_id:
            try:
                equip = Equip.objects.get(pk=int(equip_id))
                PronosticEquipFase.objects.get_or_create(
                    jugador=jugador,
                    fase=fase,
                    equip=equip,
                    defaults={'posicio': 0},
                )
            except (Equip.DoesNotExist, ValueError):
                pass


def _guarda_equips_posicio_fase(request, jugador, fase, posicions):
    PronosticEquipFase.objects.filter(jugador=jugador, fase=fase).delete()
    for posicio in posicions:
        equip_id = request.POST.get(f'equip_{posicio}')
        if equip_id:
            try:
                equip = Equip.objects.get(pk=int(equip_id))
                PronosticEquipFase.objects.get_or_create(
                    jugador=jugador,
                    fase=fase,
                    equip=equip,
                    defaults={'posicio': posicio},
                )
            except (Equip.DoesNotExist, ValueError):
                pass
