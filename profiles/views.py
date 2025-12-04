from django.shortcuts import render

# Create your views here.
def profile(request):
    """display users profile"""
    template = 'profiles/profile.html'
    context = {}

    return render(request, template, context)