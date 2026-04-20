from django.shortcuts import render, redirect
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
    def get(self, request):
        logout(request)
        return redirect('/login/')

class SeccionCarpetaListView(LoginRequiredMixin, View):
    def get(self, request, seccion):
        return render(request, 'list/list.html', {
            'carpetas': Carpeta.objects.filter(seccion__pk=seccion),
            'seccion': Seccion.objects.get(pk=seccion),
            'form_carpeta': CrearCarpetaForm(prefix='carpeta'),
            'no_crear_archivo': True
        })
    
    def post(self, request, seccion):
            nombre_carpeta = request.POST.get('carpeta-nombre')

            if(nombre_carpeta):
                form_carpeta = CrearCarpetaForm(request.POST, prefix='carpeta')

                with transaction.atomic():
                    if form_carpeta.is_valid():
                        form_carpeta.instance.seccion = Seccion.objects.get(pk=seccion)
                        form_carpeta.save()

                        Registro.objects.create(
                            carpeta = form_carpeta.instance,
                            accion = "C",
                            usuario = request.user,
                            descripcion = f"Creación de la carpeta {form_carpeta.instance.nombre} en la sección {form_carpeta.instance.seccion}"
                        )                        

                        return redirect(f'/list/{seccion}/')
                    else:
                        messages.error(request, 'Error al crear la carpeta.')
                        print(form_carpeta.errors)
                        return redirect(f'/list/{seccion}/')
                
                messages.error(request, 'Error al crear la carpeta.')
                return redirect(f'/list/{seccion}/')

class FileUploadView(LoginRequiredMixin, View):
    pass

class FolderCreateView(LoginRequiredMixin, View):
    pass

class FolderUpdateView(LoginRequiredMixin, View):
    pass

class FileUpdateView(LoginRequiredMixin, View):
    pass

class FileChangeStatusView(LoginRequiredMixin, View):
    pass

class SectionCreateView(LoginRequiredMixin, View):
    pass
