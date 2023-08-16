from django.urls import path, include
from .view import PostViewSet, genericCRUDAPIView
from rest_framework import routers


router = routers.SimpleRouter()

# override default basename for queryset
router.register('posts', PostViewSet, basename='posts')

# either include registered router or concatenate with urlpatterns
urlpatterns = [
    # path('posts/', genericListAPIView.as_view()),
    path('post/<int:pk>/', genericCRUDAPIView.as_view()),
    path('', include(router.urls))
]

