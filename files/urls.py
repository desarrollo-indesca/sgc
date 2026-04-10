from django.urls import path
from .views import *

urlpatterns = [
    path('', RedirectView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('list/<str:route>/', FileListView.as_view(), name='list_files'),
    path('upload/<str:route>/', FileUploadView.as_view(), name='upload_file'),
]