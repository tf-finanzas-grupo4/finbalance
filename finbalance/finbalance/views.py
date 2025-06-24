from django.shortcuts import render

def home(request):
    """View function for the home page of the site."""
    return render(request, 'home.html')
