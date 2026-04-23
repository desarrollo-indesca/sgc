from django.urls import path
from .views import *

urlpatterns = [
    path('', RedirectView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('list/', SeccionListView.as_view(), name='list_seccion'),
    path('list/<int:seccion>/', SeccionCarpetaListView.as_view(), name='list_files'),
    path('list/<int:seccion>/carpetas/<str:carpeta>/', CarpetaListView.as_view(), name='list_files_carpeta'),
]