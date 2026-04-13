from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages

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

            print(user)

            login(request, user)
        except Exception as ex:
            print(str(ex))
            messages.error(request, 'Error desconocido. Credenciales incorrectas o no autorizadas.')
            return redirect('/login')

        return redirect('/list/')

class FileListView(View):
    pass

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
