from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class RedirectView(View):
    def get(self, request):
        return redirect('/list/root/')

class LoginView(View):
    pass

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
