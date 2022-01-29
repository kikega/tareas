"""Admin modelos Tareas"""
from django.contrib import admin
from tareas.models import Tarea, Esfuerzo, Categoria

# Modificación de cabeceras del admin
admin.site.site_header = 'Panel de control Tareas Ibercom'
admin.site.index_title = 'Administración Ibercom'
admin.site.site_title = 'Admin Ibercom'

# Register your models here.
admin.site.register(Tarea)
admin.site.register(Esfuerzo)
admin.site.register(Categoria)
