"""
Modelos para la gestión de las tareas
"""
from django.db import models
# Importamos los modelos de Cliente
#from clientes.models import Cliente, Central, Modulo
# Create your models here.


class Categoria(models.Model):
    """Tipo de categoria asignada a cada tarea"""
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return str(self.nombre)


class Tarea(models.Model):
    """Tareas a realizar"""
    tarea = models.CharField('Titulo de la tarea', max_length=50)
    cliente = models.ForeignKey('clientes.Cliente', verbose_name=(
        "Clientes"), on_delete=models.CASCADE, null=True)
    central = models.ForeignKey('clientes.Central', verbose_name=(
        "Centrales"), on_delete=models.CASCADE, null=True)
    modulo = models.ForeignKey('clientes.Modulo', verbose_name=(
        "Modulos"), on_delete=models.CASCADE, null=True)
    descripcion = models.TextField()
    fecha_inicio = models.DateTimeField(
        'Fecha de creación', auto_now=False, auto_now_add=False)
    fecha_fin = models.DateTimeField(
        'Fecha finalización', auto_now=False, auto_now_add=False)
    bj = models.CharField('Número de BJ', max_length=10)
    TIPO_TAREA = (
        ('a', 'Averia'),
        ('p', 'Provisión')
    )
    tipo = models.CharField(
        choices=TIPO_TAREA, max_length=1, blank=True, null=True)
    activa = models.BooleanField(default=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, null=True)

    class Meta:
        """Ordena los resultados por fecha de inicio"""
        ordering = ['fecha_inicio']

    def __str__(self):
        return '{} - {}'.format(self.tarea, self.fecha_inicio)


class Esfuerzo(models.Model):
    """Esfuerzo realizado por cada tarea"""
    fecha_inicio = models.DateTimeField(
        'Fecha inicio', auto_now=False, auto_now_add=False)
    fecha_fin = models.DateTimeField(
        'Fecha fin', auto_now=False, auto_now_add=False)
    descripcion = models.TextField()
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE)
    incidencia = models.BooleanField(default=False)

    class Meta:
        """Ordena los resultados por fecha de inicio"""
        ordering = ['fecha_inicio']

    def __str__(self):
        return str(self.tarea)
