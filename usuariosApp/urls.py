from django.urls import path

from usuariosApp.views import SignUpView
from usuariosApp import views


urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path('', views.index, name='home'),  # Página principal que muestra las criptomonedas

]