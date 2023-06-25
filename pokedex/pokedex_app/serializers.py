from .models import Pokemon
from rest_framework import serializers


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pokemon
        fields = ['name', 'mon_type']

class PokemonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pokemon
        fields = '__all__'
