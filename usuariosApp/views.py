from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.generic import CreateView
from rest_framework.reverse import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from .models import Favorite, Crypto, Portafolio, Transaction
from django.core.paginator import Paginator
import requests
from decimal import Decimal
from django.db import IntegrityError
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

    # Obtener las criptomonedas favoritas del usuario basadas en el `symbol` (no el id)
    user_favorites = Favorite.objects.filter(user=request.user).values_list('crypto__symbol', flat=True)

    # Paginación
    paginator = Paginator(criptomonedas, 50)  # Paginación de 50 elementos por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'index.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'user_favorites': user_favorites,  # Esta variable ya contiene los `symbol` de los favoritos
    })



# Vista para agregar un favorito
@login_required
def add_to_favorites(request, crypto_symbol):
    try:
        # Intenta obtener la criptomoneda por el símbolo
        crypto = Crypto.objects.get(symbol__iexact=crypto_symbol)  # Busca por símbolo, sin importar mayúsculas/minúsculas
    except Crypto.DoesNotExist:
        # Si no existe en la base de datos, obtenerla desde la API de CoinGecko
        url = f'https://api.coingecko.com/api/v3/coins/markets'
        params = {'vs_currency': 'usd', 'symbols': crypto_symbol.lower()}  # Convertir el símbolo a minúsculas
        response = requests.get(url, params=params)

        if response.status_code == 200:
            crypto_data = response.json()
            if crypto_data:  # Si se obtiene datos
                crypto_info = crypto_data[0]  # Tomamos la primera criptomoneda de la respuesta

                # Verificar si el precio está presente antes de guardar
                if 'current_price' not in crypto_info or crypto_info['current_price'] is None:
                    return render(request, 'index.html', {'error': f"No se pudo obtener el precio de {crypto_symbol}."})

                # Guardamos la nueva criptomoneda en la base de datos
                crypto = Crypto.objects.create(
                    symbol=crypto_info['symbol'],
                    name=crypto_info['name'],
                    current_price=crypto_info['current_price'],
                    market_cap=crypto_info['market_cap'],
                    image_url=crypto_info.get('image', ''),  # Usa el valor por defecto si no está presente
                )
            else:
                return render(request, 'index.html', {'error': f"No se encontró la criptomoneda con símbolo {crypto_symbol}."})
        else:
            return render(request, 'index.html', {'error': f"Error al obtener datos de la API para {crypto_symbol}."})

    # Verificar si la criptomoneda ya está en favoritos
    favorite_exists = Favorite.objects.filter(user=request.user, crypto=crypto).exists()

    if not favorite_exists:
        # Si no está en favoritos, agregarla
        Favorite.objects.create(user=request.user, crypto=crypto)
        return redirect('favorites_list')  # Redirigir a la página de favoritos
    else:
        return render(request, 'index.html', {'error': f"La criptomoneda {crypto_symbol} ya está en tus favoritos."})


def remove_from_favorites(request, crypto_symbol):
    try:
        # Buscar la criptomoneda por su símbolo
        crypto = Crypto.objects.get(symbol__iexact=crypto_symbol)
    except Crypto.DoesNotExist:
        return render(request, 'index.html', {'error': f"No se encontró la criptomoneda con símbolo {crypto_symbol}."})

    # Eliminar el registro de favorito
    Favorite.objects.filter(user=request.user, crypto=crypto).delete()

    return redirect('favorites_list')  # Redirige a la página de favoritos


@login_required
def favorites_list(request):
    # Obtenemos las criptomonedas favoritas del usuario logueado
    favorites = Favorite.objects.filter(user=request.user)

    # Lista de criptomonedas favoritas
    favorite_cryptos = [favorite.crypto for favorite in favorites]

    return render(request, 'favorites_list.html', {'favorite_cryptos': favorite_cryptos})


@login_required
def add_to_portafolio(request):
    if request.method == 'POST':
        crypto_symbol = request.POST.get('crypto_symbol')
        quantity = request.POST.get('quantity')

        try:
            crypto = Crypto.objects.get(symbol__iexact=crypto_symbol)
        except Crypto.DoesNotExist:
            return render(request, 'error.html', {'error': 'Criptomoneda no encontrada'})

        # Convert quantity to Decimal to avoid type errors
        quantity = Decimal(quantity)

        # Verificar si ya existe en el portafolio
        portafolio_item, created = Portafolio.objects.get_or_create(user=request.user, crypto=crypto)

        # Actualizar la cantidad en el portafolio
        portafolio_item.quantity += quantity
        portafolio_item.save()

        return redirect('portafolio_view')

    cryptos = Crypto.objects.all()  # Obtener todas las criptomonedas
    return render(request, 'add_to_portafolio.html', {'cryptos': cryptos})
@login_required
def portafolio_view(request):
    # Obtener el portafolio del usuario actual
    portafolio = Portafolio.objects.filter(user=request.user, quantity__gt=0)

    total_value = 0
    total_profit_loss = 0

    # Calcular el valor total del portafolio y las ganancias/pérdidas
    for item in portafolio:
        total_value += item.current_value()
        total_profit_loss += item.profit_loss()

    return render(request, 'portafolio.html', {
        'portfolio': portafolio,  # Asegúrate de que 'portfolio' está pasando correctamente
        'total_value': total_value,
        'total_profit_loss': total_profit_loss
    })




@login_required
def vender_portafolio(request, portafolio_id):
    # Get the portafolio item based on the provided id
    portafolio_item = Portafolio.objects.get(id=portafolio_id)

    # Get the quantity to be sold from the form
    quantity_vendida = request.POST.get('cantidad_vendida')

    # Convert quantity to Decimal to prevent type mismatch errors
    quantity_vendida = Decimal(quantity_vendida)

    # Check if the user is trying to sell more than they have
    if quantity_vendida > portafolio_item.quantity:
        return render(request, 'error.html', {'error': 'No tienes suficientes criptomonedas para vender'})

    # Subtract the sold quantity from the portfolio
    portafolio_item.quantity -= quantity_vendida

    # If quantity is zero, remove the item from the portfolio
    if portafolio_item.quantity == 0:
        portafolio_item.delete()
    else:
        portafolio_item.save()

    # Optionally, log the transaction (not implemented here)
    # Transaction.objects.create(user=request.user, action="sell", crypto=portafolio_item.crypto, quantity=quantity_vendida)

    return redirect('portafolio_view')


@login_required
def comprar_portafolio(request, portafolio_id):
    # Get the portafolio item based on the provided id
    portafolio_item = Portafolio.objects.get(id=portafolio_id)

    # Get the quantity of the cryptocurrency to be bought from the form
    quantity_comprada = request.POST.get('cantidad_comprada')

    # Convert quantity to Decimal to prevent type mismatch errors
    quantity_comprada = Decimal(quantity_comprada)

    # Update the quantity in the portfolio (add the purchased amount)
    portafolio_item.quantity += quantity_comprada
    portafolio_item.save()

    # Optionally, log the transaction (not implemented here)
    # Transaction.objects.create(user=request.user, action="buy", crypto=portafolio_item.crypto, quantity=quantity_comprada)

    return redirect('portafolio_view')

@login_required
def transaction_history(request):
    # Obtener todas las transacciones del usuario
    transactions = Transaction.objects.filter(user=request.user).order_by('-transaction_date')

    return render(request, 'transaction_history.html', {
        'transactions': transactions
    })

def is_superuser(user):
    return user.is_superuser  # Verifica si el usuario tiene privilegios de superusuario

@user_passes_test(is_superuser)  # Solo los superusuarios podrán acceder
def user_list(request):
    users = User.objects.all()  # Obtener todos los usuarios
    return render(request, 'admin/user_list.html', {'users': users})

class SignUpView(SuccessMessageMixin, CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
    success_message = "¡Usuario creado exitosamente!"