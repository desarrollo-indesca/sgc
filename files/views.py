from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction

from .models import Seccion, Archivo, Carpeta, Registro
from .forms import *

# Create your views here.

class RedirectView(View):
    def get(self, request):
        return redirect('/login/')

class LoginView(View):
    """
    Resumen:
    Clase que maneja el inicio de sesión.
    
    Atributos:
    - Ninguno
    
    Métodos:
    - get: Método que muestra el formulario de inicio de sesión.
    - post: Método que verifica las credenciales del usuario y, si son válidas, inicia la sesión y redirige al usuario a la página principal.
    """
    def get(self, request):
        if(request.user.is_authenticated):
            return redirect('/list/')

        return render(request, 'login.html')
        
    def post(self, request):
        try:
            user = authenticate(
                request,
                username = request.POST.get('username'),
                password = request.POST.get('password')
            )

            login(request, user)
        except Exception as ex:
            print(str(ex))
            messages.error(request, 'Error desconocido. Credenciales incorrectas o no autorizadas.')
            return redirect('/login')

        return redirect('/list/')

class SeccionListView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'list/list_secciones.html', {
            'secciones': Seccion.objects.all(),
        })
    
class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        return redirect('/login/')

class SeccionCarpetaListView(LoginRequiredMixin, View):
    def get(self, request, seccion):
        return render(request, 'list/list.html', {
            'carpetas': Carpeta.objects.filter(seccion__pk=seccion, activo=True),
            'archivos': Archivo.objects.filter(seccion__pk=seccion, estado__in=['P', 'B']),
            'seccion': Seccion.objects.get(pk=seccion),
            'form_carpeta': CrearCarpetaForm(prefix='carpeta'),
            'form_archivo': CrearArchivoForm(prefix='archivo'),
        })
    
    def post(self, request, seccion):
        if(request.user.is_superuser):
                archivo = request.POST.get('archivo')
                nombre_carpeta = request.POST.get('carpeta-nombre')
                eliminar = request.POST.get('eliminar')
                editar = request.POST.get('editar')
                
                with transaction.atomic():
                    if(archivo):
                        print("Archivo")
                        if(eliminar):
                            print("Eliminar")
                            archivo = Archivo.objects.get(pk=eliminar)
                            archivo.estado = "E"
                            archivo.save()

                            Registro.objects.create(
                                archivo = archivo,
                                accion = "E",
                                usuario = request.user,
                                descripcion = f"Eliminación del archivo {archivo.nombre} en la sección {archivo.seccion}"
                            )

                            messages.success(request, 'Archivo eliminado. Solo podrá visualizarse o restauren los registros de cambios.')
                            return redirect(f'/list/{seccion}/')
                             
                        form_archivo = CrearArchivoForm(request.POST, request.FILES, prefix='archivo')
                        
                        try:
                            if form_archivo.is_valid():
                                    form_archivo.instance.seccion = Seccion.objects.get(pk=seccion)
                                    form_archivo.instance.save()

                                    Registro.objects.create(
                                        archivo = form_archivo.instance,
                                        accion = "C",
                                        usuario = request.user,
                                        descripcion = f"Creación del archivo {form_archivo.instance.nombre} en la sección {form_archivo.instance.seccion}",
                                    )

                                    messages.success(request, 'Archivo creado.')
                                    return redirect(f'/list/{seccion}/')
                            else:
                                    messages.error(request, f'Error al crear el archivo: {form_archivo.errors}')
                                    print(form_archivo.errors)
                                    return redirect(f'/list/{seccion}/')
                        except Exception as ex:
                            messages.error(request, f'Error al crear el archivo: {str(ex)}')
                            return redirect(f'/list/{seccion}/')
                    elif(eliminar):
                        carpeta = Archivo.objects.get(pk=eliminar)
                        archivo.activo = False
                        carpeta.save()

                        Registro.objects.create(
                            carpeta = carpeta,
                            accion = "E",
                            usuario = request.user,
                            descripcion = f"Eliminación de la carpeta {carpeta.nombre} en la sección {carpeta.seccion}"
                        )

                        messages.success(request, 'Carpeta eliminada.')
                        return redirect(f'/list/{seccion}/')
                    elif(editar):
                        carpeta = Carpeta.objects.get(pk=editar)
                        name_old = carpeta.nombre
                        
                        try:
                                carpeta.nombre = request.POST.get('carpeta-nombre')
                                carpeta.save()

                                Registro.objects.create(
                                    carpeta = carpeta,
                                    accion = "U",
                                    usuario = request.user,
                                    descripcion = f"Edición de la carpeta {name_old} a {carpeta.nombre} en la sección {carpeta.seccion}"
                                )              

                                messages.success(request, 'Carpeta editada.')
                                return redirect(f'/list/{seccion}/')
                        except Exception as ex:
                            messages.error(request, f'Error al crear la carpeta: {str(ex)}')
                            return redirect(f'/list/{seccion}/')


                    if(nombre_carpeta and not editar):
                        form_carpeta = CrearCarpetaForm(request.POST, prefix='carpeta')
                        
                        try:
                            if form_carpeta.is_valid():
                                    form_carpeta.instance.seccion = Seccion.objects.get(pk=seccion)
                                    form_carpeta.save()

                                    Registro.objects.create(
                                        carpeta = form_carpeta.instance,
                                        accion = "C",
                                        usuario = request.user,
                                        descripcion = f"Creación de la carpeta {form_carpeta.instance.nombre} en la sección {form_carpeta.instance.seccion}"
                                    )

                                    messages.success(request, 'Carpeta creada.')
                                    return redirect(f'/list/{seccion}/')
                            else:
                                    messages.error(request, 'Error al crear la carpeta.')
                                    print(form_carpeta.errors)
                                    return redirect(f'/list/{seccion}/')
                        except Exception as ex:
                            messages.error(request, f'Error al crear la carpeta: {str(ex)}')
                            return redirect(f'/list/{seccion}/')
                    elif(eliminar):
                        carpeta = Carpeta.objects.get(pk=eliminar)
                        carpeta.activo = False
                        carpeta.save()

                        Registro.objects.create(
                            carpeta = carpeta,
                            accion = "E",
                            usuario = request.user,
                            descripcion = f"Eliminación de la carpeta {carpeta.nombre} en la sección {carpeta.seccion}"
                        )

                        messages.success(request, 'Carpeta eliminada.')
                        return redirect(f'/list/{seccion}/')
                    elif(editar):
                        carpeta = Carpeta.objects.get(pk=editar)
                        name_old = carpeta.nombre
                        
                        try:
                                carpeta.nombre = request.POST.get('carpeta-nombre')
                                carpeta.save()

                                Registro.objects.create(
                                    carpeta = carpeta,
                                    accion = "U",
                                    usuario = request.user,
                                    descripcion = f"Edición de la carpeta {name_old} a {carpeta.nombre} en la sección {carpeta.seccion}"
                                )              

                                messages.success(request, 'Carpeta editada.')
                                return redirect(f'/list/{seccion}/')
                        except Exception as ex:
                            messages.error(request, f'Error al crear la carpeta: {str(ex)}')
                            return redirect(f'/list/{seccion}/')

class CarpetaListView(LoginRequiredMixin, View):
    def get(self, request, seccion, carpeta):

        direcciones = carpeta.split('/')
    
        # Get the root folder or 404
        carpeta_padre = get_object_or_404(
            Carpeta, 
            seccion__pk=seccion, 
            nombre=direcciones[0], 
            activo=True
        )

        # Traverse the path; if any step fails, it raises a 404
        for i in range(1, len(direcciones)):
            carpeta_padre = get_object_or_404(
                Carpeta, 
                seccion__pk=seccion, 
                carpeta=carpeta_padre, 
                nombre=direcciones[i], 
                activo=True
            )

        # Get the section or 404
        seccion_obj = get_object_or_404(Seccion, pk=seccion)

        return render(request, 'list/list.html', {
            'carpetas': Carpeta.objects.filter(carpeta=carpeta_padre, activo=True),
            'archivos': Archivo.objects.filter(carpeta=carpeta_padre, estado__in=['P', 'B']),
            'seccion': seccion_obj,
            'form_carpeta': CrearCarpetaForm(prefix='carpeta'),
            'form_archivo': CrearArchivoForm(prefix='archivo'),
            'ruta_carpeta': carpeta_padre.ruta_lista(),
        })
