from django.urls import path, include
from .views import InventoryView, PokemonView


app_name = 'pokedex'

urlpatterns = [
    path('', InventoryView.as_view(), name="inventory"),
    path('<int:pk>/', PokemonView.as_view(), name="pokemon")
]
