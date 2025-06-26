from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def login_view(request):
    """View function for the login page."""
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenido {username}!")
                return redirect('home')
            else:
                messages.error(request, "Usuario o contraseña inválidos.")
        else:
            messages.error(request, "Usuario o contraseña inválidos.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})

def signup_view(request):
    """View function for the signup page."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Cuenta creada para {username}!")
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Error en el registro. Por favor verifica la información.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'authentication/signup.html', {'form': form})
