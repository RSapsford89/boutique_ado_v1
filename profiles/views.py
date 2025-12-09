from django.shortcuts import render, get_object_or_404
from django.contrib import messages

from .models import UserProfile
from .forms import UserProfileForm 
from checkout.models import Order

# Create your views here.
def profile(request):
    """display users profile"""
    profile = get_object_or_404(UserProfile, user=request.user)
    form = UserProfileForm(instance=profile)
    orders = profile.orders.all()

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
    
    form = UserProfileForm(instance=profile)
    orders = profile.orders.all()

    template = 'profiles/profile.html'
    context = {
        'form': form,
        'orders': orders,
        'on_profile_page': True
    }

    return render(request, template, context)


def order_history(request, order_number):
    """
    Docstring for order_history return user's order history
    from Order db. 'from_profile' logic to inform traffic source
    
    :param request: Description
    :param order_number: Description
    """
    # profile = get_object_or_404(UserProfile, user=request.user)
    order_history = get_object_or_404(Order, order_number=order_number)
    messages.info(request, (
        f'This is a past confirmation for order {order_number}'
    ))
    template = 'checkout/checkout_success.html'
    context = {
        'order': order_history,
        'from_profile': True,
    }

    return render(request, template, context)