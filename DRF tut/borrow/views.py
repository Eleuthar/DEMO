from .models import Friend, Belonging, Borrowed
from .serializer import FriendSerializer, BelongingSerializer, BorrowingSerializer
from rest_framework.viewsets import ModelViewSet


class FriendViewSet(ModelViewSet):
	queryset = Friend.objects.all()
	serializer_class = FriendSerializer

	
class BelongingViewSet(ModelViewSet):
	queryset = Belonging.objects.all()
	serializer_class = BelongingSerializer


class BorrowingViewSet(ModelViewSet):
	queryset = models.Borrowing.objects.all()
	serializer_class = BorrowingSerializer
	
