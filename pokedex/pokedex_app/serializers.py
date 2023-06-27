from .models import Pokemon, Move
from rest_framework import serializers


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pokemon
        fields = ['name', 'mon_type']

class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = '__all__'

class PokemonSerializer(serializers.ModelSerializer):
    moves = MoveSerializer(many=True)

    class Meta:
        model = Pokemon
        fields = '__all__'



