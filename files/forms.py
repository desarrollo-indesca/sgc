from django import forms

from .models import Carpeta

class CrearCarpetaForm(forms.ModelForm):
    class Meta:
        model = Carpeta
        fields = ['nombre']
