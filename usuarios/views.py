from django.shortcuts import render, redirect

# Autenticacion
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your views here.


def login_view(request):
    """Vista para hacer login en la aplicación"""
    if request.method == 'POST':
        username = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'usuarios/login.html', {'error': 'Usuario o password incorrecto'})

    return render(request, 'usuarios/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
