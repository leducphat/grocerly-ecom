from rest_framework import serializers
from core.models import Product, Category, Vendor

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['c_id', 'title', 'image']

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['v_id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    vendor = VendorSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'p_id', 'title', 'description', 'price', 'old_price', 
            'stock_count', 'weight_volume', 'ingredients', 
            'storage_instructions', 'category', 'vendor', 'image', 'in_stock'
        ]
