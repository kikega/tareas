from django.shortcuts import render

# Autenticacion
from django.contrib.auth.decorators import login_required
# Create your views here.


@login_required
def index(request):
    """Pagina principal de la palicación"""
    return render(request, 'tareas/index.html')
