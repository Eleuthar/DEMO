from rest_framework import generics
from .serializers import InventorySerializer, PokemonSerializer
from .models import Pokemon


class InventoryView(generics.ListCreateAPIView):
    serializer_class = InventorySerializer
    queryset = Pokemon.objects.all()
    template_name = 'inventory.html'
    context_object_name = 'pokemonz'

class PokemonView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Pokemon.objects.prefetch_related("moves")

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return InventorySerializer
        return PokemonSerializer
