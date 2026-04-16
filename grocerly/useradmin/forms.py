from core.models import Product
from django import forms

class AddProductForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Product Title", "class":"form-control"}))
    description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Product Description", "class":"form-control"}))
    price = forms.CharField(widget=forms.NumberInput(attrs={'placeholder': "Sale Price", "class":"form-control"}))
    old_price = forms.CharField(widget=forms.NumberInput(attrs={'placeholder': "Old Price", "class":"form-control"}))
    type = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Type of product e.g organic cream", "class":"form-control"}))
    stock_count = forms.CharField(widget=forms.NumberInput(attrs={'placeholder': "How many are in stock?", "class":"form-control"}))
    expiry_period = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Expiry period e.g 100 Days", "class":"form-control"}), required=False)
    mfd = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'placeholder': "e.g: 22-11-02", "class":"form-control"}), required=False)
    tags = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Tags", "class":"form-control"}), required=False)
    image = forms.ImageField(widget=forms.FileInput(attrs={"class":"form-control"}), required=False)
    weight_volume = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "Volume/Weight (e.g. 1kg, 500ml)", "class":"form-control"}), required=False)
    ingredients = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Ingredients list", "class":"form-control"}), required=False)
    storage_instructions = forms.CharField(widget=forms.TextInput(attrs={'placeholder': "e.g. Store in a cool dry place", "class":"form-control"}), required=False)

    class Meta:
        model = Product
        fields = [
            'title',
            'image',
            'description',
            'price',
            'old_price',
            'specification',
            'type',
            'stock_count',
            'expiry_period',
            'mfd',
            'tags',
            'category',
            'weight_volume',
            'ingredients',
            'storage_instructions',
        ]
