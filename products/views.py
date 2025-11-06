from django.shortcuts import render
from .models import Product
# Create your views here.

def all_products(request):
    """A view to show all products, including sorting and searching queries"""

    products = Product.objects.all() # Grab all the Product objects
    # The context returned to the view...
    context = {
        'products': products,
    }
    return render(request,'products/products.html',  context)