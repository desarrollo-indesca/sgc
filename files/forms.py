from django import forms

from .models import Carpeta, Archivo

class CrearCarpetaForm(forms.ModelForm):
    class Meta:
        model = Carpeta
        fields = ['nombre']

class CrearArchivoForm(forms.ModelForm):
    class Meta:
        model = Archivo
        fields = ['nombre', 'direccion']
