from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500'})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
