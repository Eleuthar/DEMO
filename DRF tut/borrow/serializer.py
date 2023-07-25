from rest_framework import serializers
from .models import Friend, Belonging, Borrowing


class FriendSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.Friend
		fields = ['id', 'name']
		
		
class BelongingSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.Belonging
		fields = ['id', 'name']


class BorrowingSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.Belonging
		fields = ['id', 'what', 'to_who', 'when', 'returned']
		

