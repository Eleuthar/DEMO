from django.shortcuts import render
from .models import Post
from .serializer import PostSerializer

# fun view 1
from django.http import JsonResponse, HttpResponse
from rest_framework.parsers import JSONParser

# fun view 2
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# CB view 1
from rest_framework.views import APIView
from django.http import Http404

#CB view 2
from rest_framework import generics
from rest_framework import mixins

# AUTH
from rest_framework.authentication import \
    SessionAuthentication,\
    BasicAuthentication,\
    TokenAuthentication
from rest_framework.permissions import IsAuthenticated

# viewset requires router
from rest_framework.viewsets import ViewSet


# ~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION VIEW 1 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#def posts_view(request):
#
#    if request.method == 'GET':
#        posts = Post.objects.all()
#        serializer = PostSerializer(posts, many=True)
#        return JsonResponse(serializer.data, safe=False)
#
#    elif request.method == 'POST':
#        data = JSONParser().parse(request)
#        serializer = PostSerializer(data = data)
#
#        if serializer.is_valid():
#            serializer.save()
#            return JsonResponse(serializer.data, status=201)
#        return JsonResponse(serializer.errors, status=400)
#    
#
#def posts_detail(request, pk):
#
#    try:
#        post = Post.objects.get(pk=pk) #instance
#    except post.DoesNotExist:
#        return HttpResponse(status=404)
#
#    if request.method == 'GET':
#        serializer = PostSerializer(post)
#        return JsonResponse(serializer.data)

#    elif request.method == 'PUT':
#        data = JSONParser().parse(request)
#        serializer = PostSerializer(post, data=data)
#
#        if serializer.is_valid():
#            serializer.save()
#            return JsonResponse(serializer.data)
#        return JsonResponse(serializer.errors, status=400)
#
#    elif request.method == 'DELETE':
#        post.delete()
#        return HttpResponse(status=204) #no content



# ~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION VIEW 2 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#@api_view(['GET', 'POST']) # ALLOW ONLY GET & POST
#def posts_view(request):
#
#    if request.method == 'GET':
#        posts = Post.objects.all()
#        serializer = PostSerializer(posts, many=True)
#        return Response(serializer.data)
#
#    elif request.method == 'POST':
#        serializer = PostSerializer(data = request.data)
#
#        if serializer.is_valid():
#            serializer.save()
#            return Response(serializer.data, status=status.HTTP_201_CREATED)
#        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
#    
#
#@api_view(['GET', 'PUT', 'DELETE'])
#def post_detail(request, pk):
#
#    try:
#        post = Post.objects.get(pk=pk) #instance
#    except post.DoesNotExist:
#        return Response(status=HTTP_404_NOT_FOUND)
#
#    if request.method == 'GET':
#        serializer = PostSerializer(post)
#        return Response(serializer.data)
#
#    elif request.method == 'PUT':
#        serializer = PostSerializer(post, data=request.data)
#
#        if serializer.is_valid():
#            serializer.save()
#            return Response(serializer.data)
#        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
#
#    elif request.method == 'DELETE':
#        post.delete()
#        return HttpResponse(status=204) #no content


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CB VIEW 1 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

class PostsAPIView(APIView):
    
    def get(self, request):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        
class PostDetailAPIView(APIView):
    
    def get_object(self, pk):
        try:
            return Post.objects.get(pk=pk) # instance
        except Post.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        post = self.get_object(pk)
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        post = self.get_object(pk)
        serializer = PostSerializer(post, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        post = self.get_object(pk)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CB VIEW 2 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

#class genericListAPIView(
#        generics.GenericAPIView,
#        mixins.ListModelMixin
#    ):
#    serializer_class = PostSerializer
#    queryset = Post.objects.all() 
#    authentication_classes = [SessionAuthentication, BasicAuthentication]
#    permission_classes = [IsAuthenticated]
#
#    def get(self, request):
#        return self.list(request)
#
#
class genericCRUDAPIView(
        generics.GenericAPIView, 
        mixins.CreateModelMixin,
        mixins.UpdateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.DestroyModelMixin,
    ):
    serializer_class = PostSerializer
    queryset = Post.objects.all() 
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    # or replace with TokenAuthentication
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return self.retrieve(request, pk)

    def post(self, request):
        return self.create(request)

    def put(self, request):
        return self.update(request)

    def delete(self, request, pk):
        return self.delete(request, pk)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ VIEWSET ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

class PostViewSet(ViewSet):

    def list(self, request):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = PostSerializer(data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
    



