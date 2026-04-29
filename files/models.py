import os
import uuid
from django.utils.text import slugify
from django.utils.encoding import smart_str

from django.db import models
from django.conf import settings

# Create your models here.

class Seccion(models.Model):
    nombre = models.CharField(max_length=255)
    def __str__(self):
        return self.nombre
    
class Carpeta(models.Model):
    nombre = models.CharField(max_length=255)
    carpeta = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='carpetas')
    seccion = models.ForeignKey(Seccion, on_delete=models.SET_NULL, null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    
    def fecha_de_carga(self):
        return self.registros.get(accion='C').fecha if self.registros.filter(accion='C').exists() else None
    
    def creado_por(self):
        return self.registros.get(accion='C').usuario if self.registros.filter(accion='C').exists() else None
    
    def carpeta_vacia(self):
        return self.archivos.filter(estado="P").count() == 0 and self.carpetas.filter(activo=True).count() == 0
    
    def ruta(self):
        if self.carpeta:
            return f"{self.carpeta.ruta()}/{self.nombre}"
        else:
            return self.nombre
        
    def ruta_lista(self):
        if self.carpeta:
            return self.carpeta.ruta_lista() + [self]
        else:
            return [self]
        
    def seccion_padre(self):
        if(not self.seccion):
            return self.carpeta.seccion_padre()
        else:
            print("Carpeta sin sección padre:", self.nombre, self.seccion)
            return self.seccion

    def ruta_anterior(self):
        ruta = self.ruta_lista()
        return "/".join([c.nombre for c in ruta[:-1]]) if len(ruta) > 1 else ""
    
class Archivo(models.Model):
    nombre = models.CharField(max_length=255)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE, related_name='archivos', null=True, blank=True)
    version_siguiente = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versiones_anteriores')
    estado = models.CharField(max_length=1, default='P') # 'P' Publicado, 'B' Borrador, 'E' Eliminado 
    seccion = models.ForeignKey(Seccion, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre
    
    def fecha_de_carga(self):
        return self.registros.get(accion='C').fecha if self.registros.filter(accion='C').exists() else None
    
    def creado_por(self):
        return self.registros.get(accion='C').usuario if self.registros.filter(accion='C').exists() else None
    
    def seccion_padre(self):
        if(not self.seccion):
            return self.carpeta.seccion_padre()
        else:
            print("Archivo sin sección padre:", self.nombre, self.seccion)
            return self.seccion

    def upload(self, *args, **kwargs):
        # 1. Clean folder names
        seccion_nom = self.seccion.nombre if self.seccion else ""
        carpeta_nom = self.carpeta.nombre if self.carpeta else ""

        root = slugify(seccion_nom).replace("-", "_").upper()
        sub_carpeta = slugify(carpeta_nom).replace("-", "_").upper()

        # 2. Handle the filename SAFELY for Debian
        original_full_name = os.path.basename(self.direccion.name)
        name, extension = os.path.splitext(original_full_name)
        
        # We slugify the NAME but keep the extension
        # This prevents 'ñ' or 'á' from ever reaching the filesystem
        clean_name = slugify(name)
        uid = uuid.uuid4().hex
        
        # If slugify returns an empty string (e.g. file was named "ñ.pdf") 
        # we use the UID as the name
        nuevo_filename = f"{uid}-{clean_name}{extension}" if clean_name else f"{uid}{extension}"

        # 3. Join using smart_str to be safe
        partes_ruta = [smart_str(p) for p in [root, sub_carpeta, nuevo_filename] if p]
        full_path = os.path.join(*partes_ruta)

        return full_path.lstrip('/')
    
    direccion = models.FileField(upload_to=upload)

class Registro(models.Model):
    archivo = models.ForeignKey(Archivo, on_delete=models.CASCADE, related_name='registros', null=True, blank=True)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE, related_name='registros', null=True, blank=True)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE, related_name='registros', null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=1, choices=[('C', 'Creación'), ('U', 'Modificación'), ('E', 'Eliminación')]) # 'C' Creación, 'U' Modificación, 'E' Eliminación
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Cambio en {self.archivo.nombre if self.archivo else self.carpeta.nombre} por {self.usuario} el {self.fecha}"
    
    class Meta:
        ordering = ['-fecha']