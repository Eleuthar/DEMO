from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import generics
from .serializers import InventorySerializer, PokemonSerializer
from .models import Pokemon

class InventoryView(generics.ListAPIView):
    serializer_class = InventorySerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'inventory.html'

    def list(self, request, *args, **kwargs):
        queryset = Pokemon.objects.all()
        return Response({'pokemons': queryset})

class CRUDPokemonView(generics.CreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PokemonSerializer
    queryset = Pokemon.objects.all()
