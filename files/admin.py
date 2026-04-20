from django.contrib import admin
from .models import Carpeta, Seccion, Archivo

# Register your models here.

admin.site.register(Carpeta)
admin.site.register(Seccion)
admin.site.register(Archivo)