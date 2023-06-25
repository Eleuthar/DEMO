from django.urls import path, include
from .views import InventoryView, CRUDPokemonView

app_name = 'pokedex'

urlpatterns = [
    path('inventory/', InventoryView.as_view(), name="inventory"),
    path('pokemon/new/', CRUDPokemonView.as_view(), name="pokemon_create"),
    path('pokemon/<int:pk>/', CRUDPokemonView.as_view(), name="pokemon_detail"),
    path('pokemon/update/<int:pk>/', CRUDPokemonView.as_view(), name="pokemon_update"),
    path('pokemon/delete/<int:pk>/', CRUDPokemonView.as_view(), name="pokemon_delete")
]
