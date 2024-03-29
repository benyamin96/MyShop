from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .pagination import DefaultPagination
from .permissions import IsAdminOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .filters import UnitPriceFilter
from .serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CollectionSerializer, CustomerSerializer,\
                         ProductSerializer, ReviewSerializer, UpdateCartItemSerializer



class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class=ProductSerializer
    filter_backends=[DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class=UnitPriceFilter
    pagination_class=DefaultPagination
    search_fields=['title','description']
    ordering_fields=['unit_price','last_update']
    permission_classes=[IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=self.kwargs['pk']).count() > 0:
            return Response({'error':'Product Can not be deleted!'}, status=405)
        return super().destroy(request, *args, **kwargs)


class CollectionViewSet(ModelViewSet):
    queryset=Collection.objects.annotate(product_count=Count('products')).all()
    serializer_class=CollectionSerializer
    permission_classes=[IsAdminOrReadOnly]
    
    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=self.kwargs['pk']).exists():
            return Response({'error':'Collection can not be deleted!'}, status=405)
        return super().destroy(request, *args, **kwargs)
    

class ReviewViewSet(ModelViewSet):
    serializer_class=ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id = self.kwargs['product_pk'])
    
    def get_serializer_context(self):
        return {'product_id':self.kwargs['product_pk']}


class CartViewSet(CreateModelMixin,
                    RetrieveModelMixin,
                    DestroyModelMixin,
                    GenericViewSet):
    queryset=Cart.objects.prefetch_related('items__product').all()
    serializer_class=CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        cart_id=self.kwargs['cart_pk']
        return CartItem.objects.filter(cart_id=cart_id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer
    
    def get_serializer_context(self):
        return {'cart_id':self.kwargs['cart_pk']}


class CustomerViewSet(CreateModelMixin,
                        RetrieveModelMixin,
                        UpdateModelMixin,
                        GenericViewSet):
    queryset=Customer.objects.all()
    serializer_class=CustomerSerializer
    permission_classes=[IsAdminUser]

    @action(detail=False, methods=['GET','PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer=get_object_or_404(Customer, user_id=request.user.id)
        if request.method == 'GET':
            serializer=CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer=CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
