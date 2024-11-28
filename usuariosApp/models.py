from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Crypto(models.Model):
    symbol = models.CharField(max_length=10, unique=True)  # Hacemos que el symbol sea único
    name = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=20, decimal_places=2)
    market_cap = models.BigIntegerField()
    image_url = models.URLField(null=True, blank=True)  # Permite valores nulos y en blanco
    initial_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)  # Precio inicial

    def __str__(self):
        return self.name

class Favorite(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    crypto = models.ForeignKey(Crypto, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.crypto.name}"

class Portafolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crypto = models.ForeignKey(Crypto, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)  # Cantidad de la criptomoneda

    def __str__(self):
        return f"{self.user.username} - {self.crypto.name} - {self.quantity}"

    # Método para calcular el valor actual del portafolio de esta criptomoneda
    def current_value(self):
        if self.crypto.current_price is not None:
            return self.crypto.current_price * self.quantity
        else:
            return Decimal(0)  # Si no tiene precio, devolvemos 0

    # Método para calcular las ganancias/pérdidas
    def profit_loss(self):
        if self.crypto.current_price is not None and self.crypto.initial_price is not None:
            initial_value = self.quantity * self.crypto.initial_price  # Debes tener un precio inicial almacenado
            return self.current_value() - initial_value
        return Decimal(0)  # Si alguno de los precios es None, devolvemos 0


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crypto = models.ForeignKey(Crypto, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)  # Provide a default value
    transaction_type = models.CharField(max_length=10, choices=[('buy', 'Comprar'), ('sell', 'Vender')])
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} {self.quantity} {self.crypto.name}"
