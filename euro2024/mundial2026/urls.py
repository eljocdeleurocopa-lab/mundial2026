"""euro2024 URL Configuration"""
from django.contrib import admin
from django.urls import include, path
from joc.views.simulacio_admin import simulacio_view
from joc.views.exporta_pronostics import exporta_pronostics

urlpatterns = [
    path('admin/simulacio/', simulacio_view, name='simulacio'),
    path('admin/exporta-pronostics/', exporta_pronostics, name='exporta_pronostics'),  # ← aquí
    path('admin/', admin.site.urls),
    path('', include('joc.urls', namespace='joc')),
    path('registration/', include('django_registration.backends.approval.urls')),
    path('registration/', include('django.contrib.auth.urls')),
]
