from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.generic import CreateView
from rest_framework.reverse import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect, get_object_or_404
from .models import Favorite, Crypto, Portafolio, Transaction
from django.core.paginator import Paginator
import requests
from decimal import Decimal
from django.db import IntegrityError
# Create your views here.

def fetch_and_save_cryptos():
    # URL de la API de CoinGecko
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 250,  # Número de criptomonedas a obtener por página
        'page': 1  # Primera página
    }

    # Enviar la solicitud a la API
    response = requests.get(url, params=params)

    # Verificar si la respuesta es exitosa
    if response.status_code == 200:
        cryptos_data = response.json()

        # Recorrer cada criptomoneda en los datos obtenidos
        for crypto_data in cryptos_data:
            try:
                # Crear una nueva criptomoneda en la base de datos si no existe
                Crypto.objects.get_or_create(
                    crypto_id=crypto_data['id'],  # Usamos 'id' como crypto_id
                    defaults={
                        'symbol': crypto_data['symbol'],
                        'name': crypto_data['name'],
                        'current_price': crypto_data['current_price'],
                        'market_cap': crypto_data['market_cap'],
                        'image_url': crypto_data.get('image', ''),  # La URL de la imagen
                        'price_change_percentage_24h': crypto_data.get('price_change_percentage_24h', 0)}
                )
            except IntegrityError:
                # Si hay un error de integridad (por ejemplo, duplicado de 'crypto_id'), ignorarlo
                pass
    else:
        print(f"Error al obtener datos: {response.status_code}")


def update_crypto_prices():
    # URL de la API de CoinGecko
    url = 'https://api.coingecko.com/api/v3/coins/markets'

    # Obtener los 'crypto_id' de las criptomonedas almacenadas
    crypto_ids = [crypto.crypto_id for crypto in Crypto.objects.all()]

    # Si no hay criptomonedas, no hacer la solicitud
    if not crypto_ids:
        return

    params = {
        'vs_currency': 'usd',
        'ids': ','.join(crypto_ids),  # Convertir la lista de 'crypto_id' a un string separado por comas
    }

    # Enviar la solicitud a la API
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        # Recorrer las criptomonedas obtenidas
        for crypto_data in data:
            try:
                # Obtener la criptomoneda correspondiente en la base de datos
                crypto = Crypto.objects.get(crypto_id=crypto_data['id'])

                # Actualizar el precio actual
                crypto.current_price = crypto_data['current_price']

                # Actualizar el cambio de precio en 24 horas (si existe)
                crypto.price_change_percentage_24h = crypto_data.get('price_change_percentage_24h', 0)

                # Guardar los cambios en la base de datos
                crypto.save()
            except Crypto.DoesNotExist:
                # Si no existe el objeto, podemos ignorar o registrar un error
                print(f"Criptomoneda con ID {crypto_data['id']} no encontrada.")
    else:
        print(f"Error al obtener datos: {response.status_code}")


@login_required
def index(request):

    # Actualizar los precios de las criptomonedas antes de mostrar los datos
    update_crypto_prices()

    # Obtener todas las criptomonedas desde la base de datos
    criptomonedas = Crypto.objects.all()

    # Filtrar resultados según la búsqueda (si el usuario ha proporcionado un término de búsqueda)
    search_query = request.GET.get('search', '')  # Obtener el término de búsqueda
    if search_query:
        criptomonedas = criptomonedas.filter(name__icontains=search_query)  # Filtrar por nombre

    # Verificar si la respuesta contiene datos
    if not criptomonedas:
        return render(request, 'index.html', {'error': 'No se encontraron criptomonedas.'})

    # Paginación
    paginator = Paginator(criptomonedas, 50)  # Paginación de 50 elementos por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Obtener las criptomonedas favoritas del usuario basadas en el `symbol`
    user_favorites = Favorite.objects.filter(user=request.user).values_list('crypto__symbol', flat=True)

    # Añadir el color según el cambio de precio (si es positivo o negativo)
    for crypto in page_obj:
        price_change_percentage = crypto.price_change_percentage_24h

        # Si el valor es None, usa 0 como valor por defecto
        if price_change_percentage is None:
            price_change_percentage = 0  # Si no hay valor, asigna 0

        # Asigna el color según el valor de 'price_change_percentage_24h'
        if price_change_percentage > 0:
            crypto.price_change_color = 'text-success'
        elif price_change_percentage < 0:
            crypto.price_change_color = 'text-danger'
        else:
            crypto.price_change_color = 'text-warning'  # Para un cambio de 0%, podrías usar un color neutral.

    return render(request, 'index.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'user_favorites': user_favorites,  # Esta variable contiene los `symbol` de los favoritos
    })


# Vista para agregar un favorito
@login_required
def add_to_favorites(request, crypto_id):
    try:
        # Buscar la criptomoneda usando el crypto_id (que es alfanumérico)
        crypto = get_object_or_404(Crypto, crypto_id=crypto_id)
    except Crypto.DoesNotExist:
        return render(request, 'index.html', {'error': f"No se encontró la criptomoneda con ID {crypto_id}."})

    # Verificar si la criptomoneda ya está en favoritos
    favorite_exists = Favorite.objects.filter(user=request.user, crypto=crypto).exists()

    if not favorite_exists:
        # Si no está en favoritos, agregarla
        Favorite.objects.create(user=request.user, crypto=crypto)
        return redirect('favorites_list')  # Redirigir a la página de favoritos
    else:
        return render(request, 'index.html', {'error': f"La criptomoneda {crypto.name} ya está en tus favoritos."})


@login_required
def remove_from_favorites(request, crypto_id):
    try:
        # Buscar la criptomoneda usando el crypto_id (que es alfanumérico)
        crypto = get_object_or_404(Crypto, crypto_id=crypto_id)
    except Crypto.DoesNotExist:
        return render(request, 'index.html', {'error': f"No se encontró la criptomoneda con ID {crypto_id}."})

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


@login_required
def crypto_details(request, crypto_id):
    # Obtener la criptomoneda desde la base de datos usando crypto_id
    crypto = get_object_or_404(Crypto, crypto_id=crypto_id)

    # Obtener más detalles de la API de CoinGecko
    url = f'https://api.coingecko.com/api/v3/coins/{crypto_id}'
    response = requests.get(url)

    if response.status_code == 200:
        details = response.json()

        # Extraer datos específicos
        description = details.get('description', {}).get('en', 'Descripción no disponible')
        current_price = details['market_data']['current_price']['usd'] if 'market_data' in details else None
        market_cap_rank = details.get('market_cap_rank', 'No disponible')
        market_cap = details['market_data']['market_cap']['usd'] if 'market_data' in details else None
        total_volume = details['market_data']['total_volume']['usd'] if 'market_data' in details else None
        price_change_percentage_24h = details['market_data']['price_change_percentage_24h'] if 'market_data' in details else None

        # Redes sociales
        twitter = details['links'].get('twitter_screen_name', '')
        reddit = details['links'].get('subreddit', '')
        github = details['links'].get('repos_url', {}).get('github', [])
        website = details['links'].get('homepage', [''])[0]

        # Si hay repositorios de GitHub, obtener el primero
        github_url = github[0] if github else None

        # Datos de suministro
        max_supply = details['market_data'].get('max_supply', 'No disponible')
        circulating_supply = details['market_data'].get('circulating_supply', 'No disponible')
        total_supply = details['market_data'].get('total_supply', 'No disponible')

        # Mercados para comprar
        markets = details.get('tickers', [])
        market_data = []
        for market in markets:
            exchange_name = market['market']['name']
            # Intentar obtener la URL del intercambio (campo trade_url)
            market_url = market.get('trade_url', None)  # trade_url es más confiable que url en algunos casos
            market_data.append({
                'exchange': exchange_name,
                'url': market_url,  # La URL que puede estar presente en trade_url
                'price': market['last']
            })

        # Paginación de los mercados
        page = request.GET.get('page', 1)  # Obtener el número de página de los parámetros GET
        paginator = Paginator(market_data, 10)  # Mostrar 10 mercados por página
        markets_page = paginator.get_page(page)  # Obtener los mercados de la página actual

        # Número de transacciones en las últimas 24 horas
        transaction_count_24h = details['market_data'].get('total_volumes', [])[0][1] if 'market_data' in details and 'total_volumes' in details['market_data'] else 'No disponible'

        # Precios históricos (últimos 30 días)
        historical_prices = []
        if 'prices' in details['market_data']:
            historical_prices = details['market_data']['prices'][:30]

    else:
        description = current_price = market_cap_rank = market_cap = total_volume = price_change_percentage_24h = None
        twitter = reddit = github_url = website = ''
        max_supply = circulating_supply = total_supply = None
        market_data = []
        transaction_count_24h = None
        historical_prices = []

    return render(request, 'crypto_details.html', {
        'crypto': crypto,
        'description': description,
        'current_price': current_price,
        'market_cap_rank': market_cap_rank,
        'market_cap': market_cap,
        'total_volume': total_volume,
        'price_change_percentage_24h': price_change_percentage_24h,
        'twitter': twitter,
        'reddit': reddit,
        'github_url': github_url,  # Pasar la URL del repositorio de GitHub
        'website': website,
        'max_supply': max_supply,
        'circulating_supply': circulating_supply,
        'total_supply': total_supply,
        'markets_page': markets_page,  # Pasar la página de mercados
        'transaction_count_24h': transaction_count_24h,
        'historical_prices': historical_prices,
    })

class SignUpView(SuccessMessageMixin, CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
    success_message = "¡Usuario creado exitosamente!"