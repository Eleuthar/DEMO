from .models import Pokemon, Move
from rest_framework import serializers


# DRF inherit serializers.ModelSerializer
class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pokemon
        fields = ['name', 'mon_type']

class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = ['move_name']

class PokemonSerializer(serializers.ModelSerializer):
    moves = MoveSerializer(many=True)

    class Meta:
        model = Pokemon
        fields = '__all__'
