"""
URL configuration for loginProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from tkinter.font import names

from django.contrib import admin
from django.urls import path, include
from usuariosApp.views import index
from usuariosApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # Todas las urls de autenticación
    path("", index, name="home"),
    path("usuarios/", include("usuariosApp.urls")),
    path('add_to_favorites/<str:crypto_symbol>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove_from_favorites/<str:crypto_symbol>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('favorites_list/', views.favorites_list, name='favorites_list'),
    path('comprar/<int:portafolio_id>/', views.comprar_portafolio, name='comprar_portafolio'),
    path('add_to_portafolio/', views.add_to_portafolio, name='add_to_portafolio'),

    path('vender/<int:portafolio_id>/', views.vender_portafolio, name='vender_portafolio'),

    path('portafolio/', views.portafolio_view, name='portafolio_view'),
    path('transaction_history/', views.transaction_history, name='transaction_history'),
    path('user_list/', views.user_list, name='user_list'),  # URL para la lista de usuarios

]
