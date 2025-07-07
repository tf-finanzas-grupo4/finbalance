from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    """View function for the home page of the site."""
    return render(request, 'home.html')
