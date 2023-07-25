from rest_framework.generics import \
	ListAPIView, CreateAPIView, RetrieveUpdateDestroyView
from .serializer import ProfileSerializer, UzrSerializer
from .models import Profile


class ProfileList(generics.ListAPIView):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all(many=True)


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer


class ProfileView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

