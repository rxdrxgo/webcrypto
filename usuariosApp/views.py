from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from rest_framework.reverse import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.core.paginator import Paginator
import requests
# Create your views here.

@login_required
def index(request):
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 250,  # Número de criptomonedas por página
        'page': request.GET.get('page', 1),  # Obtener el número de página
    }

    # Hacer la solicitud a la API
    response = requests.get(url, params=params)

    # Verificar si la respuesta fue exitosa (código de estado 200)
    if response.status_code != 200:
        return render(request, 'index.html', {'error': 'No se pudo obtener datos de la API.'})

    criptomonedas = response.json()

    # Filtrar resultados según la búsqueda
    search_query = request.GET.get('search', '')  # Obtener el término de búsqueda
    if search_query:
        criptomonedas = [crypto for crypto in criptomonedas if search_query.lower() in crypto['name'].lower()]

    # Verificar si la respuesta contiene datos
    if not criptomonedas:
        return render(request, 'index.html', {'error': 'No se encontraron criptomonedas.'})

    # Añadir la URL de la imagen a cada criptomoneda
    for crypto in criptomonedas:
        crypto['image_url'] = crypto.get('image', '')
        price_change_percentage = crypto.get('price_change_percentage_24h')

        # Si el valor es None o no es un número, usa 0 como valor por defecto
        if price_change_percentage is None or not isinstance(price_change_percentage, (int, float)):
            price_change_percentage = 0  # O cualquier valor por defecto que desees

        # Asigna el color según el valor de 'price_change_percentage_24h'
        crypto['price_change_color'] = 'text-success' if price_change_percentage > 0 else 'text-danger'

    # Paginación
    paginator = Paginator(criptomonedas, 50)  # Paginación de 50 elementos por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'index.html', {'page_obj': page_obj, 'search_query': search_query})


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
    success_message = "¡Usuario creado exitosamente!"