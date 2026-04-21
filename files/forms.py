from django import forms

from .models import Carpeta, Archivo

class CrearCarpetaForm(forms.ModelForm):
    class Meta:
        model = Carpeta
        fields = ['nombre']

class CrearArchivoForm(forms.ModelForm):
    mantener_nombre = forms.BooleanField(required=False)

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        mantener_nombre = self.cleaned_data.get('mantener_nombre')

        if not mantener_nombre:
            # Si no se mantiene el nombre, se puede modificar para evitar conflictos
            return nombre
        else:
            # Si se mantiene el nombre, se debe verificar que no exista otro archivo con el mismo nombre en la sección
            seccion = self.instance.seccion
            if Archivo.objects.filter(nombre=nombre, seccion=seccion).exists():
                raise forms.ValidationError("Ya existe un archivo con ese nombre en esta sección.")
            elif Carpeta.objects.filter(nombre=nombre, carpeta=self.instance.carpeta).exists():
                raise forms.ValidationError("Ya existe una carpeta con ese nombre en esta sección.")
            return nombre

    class Meta:
        model = Archivo
        fields = ['nombre', 'direccion']
