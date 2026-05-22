"""euro2024 URL Configuration"""
from django.contrib import admin
from django.urls import include, path
from joc.views.simulacio_admin import simulacio_view


urlpatterns = [
    path('admin/simulacio/', simulacio_view, name='simulacio'),
    path('admin/', admin.site.urls),
    path('', include('joc.urls', namespace='joc')),
    path('registration/', include('django_registration.backends.approval.urls')),
    path('registration/', include('django.contrib.auth.urls')),
]

