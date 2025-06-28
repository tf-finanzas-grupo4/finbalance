from django import forms
from .models import Bond

class BondForm(forms.ModelForm):
    class Meta:
        model = Bond
        fields = '__all__'
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'periodo_gracia': forms.DateInput(attrs={'type': 'date', 'required': False}),
            'metodo_amortizacion': forms.TextInput(attrs={'disabled': True, 'value': 'Francés'}),
        }