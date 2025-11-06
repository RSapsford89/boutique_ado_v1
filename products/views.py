from django.shortcuts import render, get_object_or_404
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


def product_detail(request, product_id):
    """A view to show individual product detail"""

    product = get_object_or_404(Product,pk=product_id) # Grab all the Product objects
    # The context returned to the view...
    context = {
        'product': product,
    }
    return render(request,'products/product_detail.html',  context)