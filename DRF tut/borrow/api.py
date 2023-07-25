from rest_framework.routers import DefaultRouter
from .views import FriendViewSet, BelongingViewSet, BorrowingViewSet


router = DefaultRouter()
router.register(r'friends', FriendViewSet)
router.register(r'belongings', BelongingViewSet)
router.register(r'borrowing', BorrowingViewSet)

