from django.db import models

# Create your models here.

class Seccion(models.Model):
    nombre = models.CharField(max_length=255)
    def __str__(self):
        return self.nombre
    
class Carpeta(models.Model):
    nombre = models.CharField(max_length=255)
    carpeta = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='carpetas')
    seccion = models.ForeignKey(Seccion, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre
    
    def fecha_de_carga(self):
        return self.registros.get(accion='C').fecha if self.registros.filter(accion='C').exists() else None
    
    def creado_por(self):
        return self.registros.get(accion='C').usuario if self.registros.filter(accion='C').exists() else None
    
class Archivo(models.Model):
    nombre = models.CharField(max_length=255)
    direccion = models.FileField(upload_to='archivos/')
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE, related_name='archivos')
    version_siguiente = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versiones_anteriores')
    estado = models.CharField(max_length=1, default='P') # 'P' Publicado, 'B' Borrador, 'E' Eliminado 

    def __str__(self):
        return self.nombre
    
    def fecha_de_carga(self):
        return self.registros.get(accion='C').fecha if self.registros.filter(accion='C').exists() else None
    
    def creado_por(self):
        return self.registros.get(accion='C').usuario if self.registros.filter(accion='C').exists() else None

class Registro(models.Model):
    archivo = models.ForeignKey(Archivo, on_delete=models.CASCADE, related_name='registros', null=True, blank=True)
    carpeta = models.ForeignKey(Carpeta, on_delete=models.CASCADE, related_name='registros', null=True, blank=True)
    seccion = models.ForeignKey(Seccion, on_delete=models.CASCADE, related_name='registros', null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=1) # 'C' Creación, 'M' Modificación, 'E' Eliminación
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Cambio en {self.archivo.nombre if self.archivo else self.carpeta.nombre} por {self.usuario} el {self.fecha}"