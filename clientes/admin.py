"""Portal de administracion de los modelos cliente"""
from django.contrib import admin
from clientes.models import Cliente, Central, Modulo

# Register your models here.


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Administracion del modelo cliente"""
    pass


@admin.register(Central)
class CentralAdmin(admin.ModelAdmin):
    """Administracion del modelo central"""
    list_display = ('cliente', 'hostname', 'tecnologia', 'ipGestion')


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    """Administracion del modelo modulo"""
    pass
