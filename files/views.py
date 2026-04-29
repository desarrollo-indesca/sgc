from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.utils.encoding import smart_str
from functools import reduce
import operator
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import Http404

from .filters import RegistroFilter
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
                        if(eliminar):
                            print("Eliminar")
                            archivo = Archivo.objects.get(pk=eliminar)
                            archivo.estado = "E"
                            archivo.save()

                            Registro.objects.create(
                                archivo = archivo,
                                accion = "E",
                                usuario = request.user,
                                descripcion = f"Eliminación del archivo '{archivo.nombre}' en la sección '{archivo.seccion}'."
                            )

                            messages.success(request, 'Archivo eliminado. Solo podrá visualizarse o restaurarse los registros de cambios.')
                            return redirect(f'/list/{seccion}/')
                        elif(editar):
                            print("Editar")
                            archivo = Archivo.objects.get(pk=editar)
                            name_old = archivo.nombre

                            form_archivo = CrearArchivoForm(request.POST, request.FILES, prefix='archivo')
                            
                            try:
                                    form_archivo.instance.seccion = Seccion.objects.get(pk=seccion)
                                    form_archivo.save()
                                    archivo.version_siguiente = form_archivo.instance
                                    archivo.estado = "R"
                                    archivo.save()

                                    Registro.objects.create(
                                        archivo = archivo,
                                        accion = "U",
                                        usuario = request.user,
                                        descripcion = f"Actualización del archivo '{name_old}' a '{archivo.nombre}' en la carpeta '{archivo.carpeta.ruta() if archivo.carpeta else 'Raíz de la sección ' + str(archivo.seccion)}'.",
                                    ) 

                                    Registro.objects.create(
                                        archivo = form_archivo.instance,
                                        accion = "C",
                                        usuario = request.user,
                                        descripcion = f"Creación del archivo '{form_archivo.instance.nombre}' en la sección '{form_archivo.instance.seccion}'; versión nueva de '{name_old}' en la carpeta '{archivo.carpeta.ruta() if archivo.carpeta else 'Raíz de la sección ' + str(archivo.seccion)}'.",
                                    )             

                                    messages.success(request, 'Archivo actualizado.')
                                    return redirect(f'/list/{seccion}/')
                            except Exception as ex:
                                messages.error(request, f'Error al editar el archivo: {str(ex)}')
                                return redirect(f'/list/{seccion}/')
                            
                        files = request.FILES.getlist('archivo-direccion')

                        for file in files:
                                form_archivo = CrearArchivoForm(request.POST, {'archivo-direccion': file}, prefix='archivo')
                                
                                try:
                                    if form_archivo.is_valid():
                                        form_archivo.instance.seccion = Seccion.objects.get(pk=seccion)
                                        form_archivo.instance.save()

                                        Registro.objects.create(
                                            archivo = form_archivo.instance,
                                            accion = "C",
                                            usuario = request.user,
                                            descripcion = f"Creación del archivo '{form_archivo.instance.nombre}' en la sección '{form_archivo.instance.seccion}'.",
                                        )
                                    else:
                                            messages.error(request, f'Error al crear el archivo: {form_archivo.errors}')
                                            print(form_archivo.errors)
                                            return redirect(f'/list/{seccion}/')
                                except Exception as ex:
                                    messages.error(request, f'Error al crear el archivo: {str(ex)}')
                                    return redirect(f'/list/{seccion}/')

                        messages.success(request, 'Archivo creado.')
                        return redirect(f'/list/{seccion}/')
                    elif(eliminar):
                        carpeta = Carpeta.objects.get(pk=eliminar)
                        carpeta.activo = False
                        carpeta.save()

                        Registro.objects.create(
                            carpeta = carpeta,
                            accion = "E",
                            usuario = request.user,
                            descripcion = f"Eliminación de la carpeta '{carpeta.nombre}' en la sección '{carpeta.seccion}'."
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
                                    descripcion = f"Edición de la carpeta '{name_old}' a '{carpeta.nombre}' en la sección '{carpeta.seccion}'."
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
                                        descripcion = f"Creación de la carpeta '{form_carpeta.instance.nombre}' en la sección '{form_carpeta.instance.seccion}'"
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
                            descripcion = f"Eliminación de la carpeta '{carpeta.nombre}' en la sección '{carpeta.seccion}'."
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
                                    descripcion = f"Edición de la carpeta '{name_old}' a '{carpeta.nombre}' en la sección '{carpeta.seccion}'."
                                )              

                                messages.success(request, 'Carpeta editada.')
                                return redirect(f'/list/{seccion}/')
                        except Exception as ex:
                            messages.error(request, f'Error al crear la carpeta: {str(ex)}')
                            return redirect(f'/list/{seccion}/')

class CarpetaListView(LoginRequiredMixin, View):
    def obtener_carpeta(self, seccion, carpeta):
        direcciones = carpeta.split('/')
    
        # Instead of get_object_or_404, use .filter().first()
        carpeta_padre = Carpeta.objects.filter(
            seccion__pk=seccion, 
            nombre=direcciones[0], 
            activo=True,
            carpeta__isnull=True # Assumes root folders have no parent
        ).first()

        if not carpeta_padre:
            print("Carpeta raíz no encontrada:", direcciones[0], "en la sección", seccion)
            raise Http404
        
        print("Carpeta raíz encontrada:", carpeta_padre)

        for i in range(1, len(direcciones)):
            carpeta_padre = Carpeta.objects.filter(
                carpeta=carpeta_padre, 
                nombre=direcciones[i], 
                activo=True
            ).first()
            
            if not carpeta_padre:
                print("Carpeta no encontrada:", direcciones[i], "en la ruta", "/".join(direcciones[:i]), "en la sección", seccion)
                raise Http404

        return carpeta_padre

    def get(self, request, seccion, carpeta):

        direcciones = carpeta.split('/')
    
        carpeta_padre = get_object_or_404(
            Carpeta, 
            seccion__pk=seccion, 
            nombre=direcciones[0], 
            activo=True
        )

        for i in range(1, len(direcciones)):
            carpeta_padre = get_object_or_404(
                Carpeta, 
                carpeta=carpeta_padre, 
                nombre=direcciones[i], 
                activo=True
            )

        seccion_obj = get_object_or_404(Seccion, pk=seccion)

        return render(request, 'list/list.html', {
            'carpetas': Carpeta.objects.filter(carpeta=carpeta_padre, activo=True),
            'archivos': Archivo.objects.filter(carpeta=carpeta_padre, estado__in=['P', 'B']),
            'seccion': seccion_obj,
            'form_carpeta': CrearCarpetaForm(prefix='carpeta'),
            'form_archivo': CrearArchivoForm(prefix='archivo'),
            'ruta_carpeta': carpeta_padre.ruta_lista(),
        })

    def post(self, request, seccion, carpeta):
        carpeta = self.obtener_carpeta(seccion, carpeta)
        print("Carpeta encontrada para POST:", carpeta)
        if(request.user.is_superuser):
                archivo = request.POST.get('archivo')
                nombre_carpeta = request.POST.get('carpeta-nombre')
                eliminar = request.POST.get('eliminar')
                editar = request.POST.get('editar')

                with transaction.atomic():
                    if(archivo):
                        if(eliminar):
                            archivo = Archivo.objects.get(pk=eliminar)
                            archivo.estado = "E"
                            archivo.save()

                            Registro.objects.create(
                                archivo = archivo,
                                accion = "E",
                                usuario = request.user,
                                descripcion = f"Eliminación del archivo '{archivo.nombre}' en la carpeta '{archivo.carpeta.ruta()}'."
                            )

                            messages.success(request, 'Archivo eliminado. Solo podrá visualizarse o restaurarse los registros de cambios.')
                            return redirect(f'/list/{seccion}/carpetas/{carpeta}/')
                        elif(editar):
                            print("Editar")
                            archivo = Archivo.objects.get(pk=editar)
                            name_old = archivo.nombre

                            form_archivo = CrearArchivoForm(request.POST, request.FILES, prefix='archivo')
                            
                            try:
                                    form_archivo.instance.carpeta = carpeta
                                    form_archivo.save()
                                    archivo.version_siguiente = form_archivo.instance
                                    archivo.estado = "R"
                                    archivo.save()

                                    Registro.objects.create(
                                        archivo = archivo,
                                        accion = "U",
                                        usuario = request.user,
                                        descripcion = f"Actualización del archivo '{name_old}' a '{archivo.nombre}' en la carpeta '{archivo.carpeta.ruta() if archivo.carpeta else 'Raíz de la sección ' + str(archivo.seccion)}'.",
                                    ) 

                                    Registro.objects.create(
                                        archivo = form_archivo.instance,
                                        accion = "C",
                                        usuario = request.user,
                                        descripcion = f"Creación del archivo '{form_archivo.instance.nombre}' en la carpeta '{form_archivo.instance.carpeta.ruta()}'; versión nueva de '{name_old}' en la carpeta '{archivo.carpeta.ruta() if archivo.carpeta else 'Raíz de la sección ' + str(archivo.seccion)}'.",
                                    )             

                                    messages.success(request, 'Archivo actualizado.')
                                    return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
                            except Exception as ex:
                                messages.error(request, f'Error al editar el archivo: {str(ex)}')
                                return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
                            
                        files = request.FILES.getlist('archivo-direccion')

                        for file in files:
                            form_archivo = CrearArchivoForm(request.POST, {'archivo-direccion': file}, prefix='archivo')
                        
                            with transaction.atomic():
                                if form_archivo.is_valid():
                                        form_archivo.instance.carpeta = carpeta
                                        form_archivo.save()

                                        Registro.objects.create(
                                            archivo = form_archivo.instance,
                                            accion = "C",
                                            usuario = request.user,
                                            descripcion = f"Creación del archivo '{form_archivo.instance.nombre}' en la ruta '{carpeta.ruta()}'.",
                                        )
                                else:
                                        messages.error(request, f'Error al crear el archivo: {form_archivo.errors}')
                                        print(form_archivo.errors)
                                        return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
                    
                        messages.success(request, 'Archivo creado.')
                        return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
                    elif(eliminar):
                        carpeta = Archivo.objects.get(pk=eliminar)
                        carpeta.activo = False
                        carpeta.save()

                        Registro.objects.create(
                            carpeta = carpeta,
                            accion = "E",
                            usuario = request.user,
                            descripcion = f"Eliminación de la carpeta '{carpeta.nombre}' en '{carpeta.ruta()}'."
                        )

                        messages.success(request, 'Carpeta eliminada.')
                        return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
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
                                    descripcion = f"Edición de la carpeta '{name_old}' a '{carpeta.nombre}' en '{carpeta.ruta()}'."
                                )              

                                messages.success(request, 'Carpeta editada.')
                                return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
                        except Exception as ex:
                            messages.error(request, f'Error al crear la carpeta: {str(ex)}')
                            return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')

                    if(nombre_carpeta and not editar):
                        form_carpeta = CrearCarpetaForm(request.POST, prefix='carpeta')
                        
                        try:
                            if form_carpeta.is_valid():
                                    form_carpeta.instance.carpeta = carpeta
                                    form_carpeta.save()

                                    Registro.objects.create(
                                        carpeta = form_carpeta.instance,
                                        accion = "C",
                                        usuario = request.user,
                                        descripcion = f"Creación de la carpeta '{form_carpeta.instance.nombre}' en '{form_carpeta.instance.ruta()}'"
                                    )

                                    messages.success(request, 'Carpeta creada.')
                                    return redirect(f'/list/{seccion}/carpetas/{form_carpeta.instance.ruta()}')
                            else:
                                    messages.error(request, 'Error al crear la carpeta.')
                                    print(form_carpeta.errors)
                                    return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
                        except Exception as ex:
                            messages.error(request, f'Error al crear la carpeta: {str(ex)}')
                            return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
                    elif(eliminar):
                        carpeta = Carpeta.objects.get(pk=eliminar)
                        carpeta.activo = False
                        carpeta.save()

                        Registro.objects.create(
                            carpeta = carpeta,
                            accion = "E",
                            usuario = request.user,
                            descripcion = f"Eliminación de la carpeta '{carpeta.nombre}' en '{carpeta.ruta()}'."
                        )

                        messages.success(request, 'Carpeta eliminada.')
                        return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
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
                                    descripcion = f"Edición de la carpeta '{name_old}' a '{carpeta.nombre}' en '{carpeta.ruta()}'."
                                )              

                                messages.success(request, 'Carpeta editada.')
                                return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')
                        except Exception as ex:
                            messages.error(request, f'Error al crear la carpeta: {str(ex)}')
                            return redirect(f'/list/{seccion}/carpetas/{carpeta.ruta()}')

class BusquedaView(LoginRequiredMixin, View):
    def get(self, request):
        busqueda = request.GET.get('busqueda')

        tokens = busqueda.split()

        if tokens:
            # 2. Create a list of Q objects: name__icontains for each token
            # This creates: Q(nombre__icontains="word1") & Q(nombre__icontains="word2")...
            query_logic = reduce(operator.and_, (Q(nombre__icontains=token) for token in tokens))
            
            # 3. Apply to your filters
            archivos = Archivo.objects.filter(query_logic, estado__in=['P', 'B'])
            carpetas = Carpeta.objects.filter(query_logic, activo=True)
        else:
            # Fallback if search is empty
            archivos = Archivo.objects.filter(estado__in=['P', 'B'])
            carpetas = Carpeta.objects.filter(activo=True)

        print(f"Resultados de búsqueda para '{busqueda}': {archivos.count()} archivos, {carpetas.count()} carpetas")
        print("Archivos encontrados:", archivos)
        print("Carpetas encontradas:", carpetas)

        return render(request, 'list/list_busqueda.html', {
            'archivos': archivos,
            'carpetas': carpetas,
            'busqueda': busqueda,
        })

class VersionesArchivoView(LoginRequiredMixin, View):
    def get(self, request, archivo):
        archivo_obj = get_object_or_404(Archivo, pk=archivo)
        versiones = []

        archivo = archivo_obj
        while archivo:
            archivo = Archivo.objects.filter(version_siguiente=archivo).first()

            if archivo:
                versiones.append(archivo)

        versiones.reverse()

        return render(request, 'modals/control-versiones.html', {
            'archivo': archivo_obj,
            'versiones': versiones,
        })

class VersionesCarpetasView(LoginRequiredMixin, View):
    def get(self, request, carpeta):
        carpeta_obj = get_object_or_404(Carpeta, pk=carpeta)

        print(carpeta_obj.registros.all())

        return render(request, 'modals/control-versiones-carpetas.html', {
            'carpeta': carpeta_obj,
            'versiones': carpeta_obj.registros.all(),
        })

class RegistroCambiosView(LoginRequiredMixin, ListView):
    paginate_by = 10
    template_name = 'list/list_registros.html'
    context_object_name = 'registros'
    model = Registro

    def get_queryset(self):
        return RegistroFilter(self.request.GET, queryset=super().get_queryset()).qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = RegistroFilter(self.request.GET, queryset=self.get_queryset())
        return ctx
