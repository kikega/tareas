"""Modelos para los clientes"""
from django.db import models

# Create your models here.


class Cliente(models.Model):
    """Clase cliente"""
    nombre = models.CharField('Nombre del cliente', max_length=50)
    coordinador = models.CharField('Coordinador', max_length=50)
    telefCoord = models.CharField('Telefono coordinador', max_length=9)
    correoCoord = models.EmailField('Correo coordinador', max_length=254)
    gestorCliente = models.CharField('Gestor cliente', max_length=50)
    telfGestor = models.CharField('Telefono gestor', max_length=50)
    telfCgp = models.CharField('Telefono cgp', max_length=50)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        """Ordena los resultados por nombre"""
        ordering = ['nombre']


class Central(models.Model):
    """Define los modelos de una central"""
    hostname = models.CharField('Hostname', max_length=50)
    raibj = models.CharField('Rai en Ciberun', max_length=50)
    TECNOLOGIA = (
        ('o', 'Alcatel OXE'),
        ('c', 'Cisco'),
        ('m', 'MX One'),
        ('u', 'Unify'),
        ('l', 'Legacy')
    )
    TIPO = (
        ('h', 'HCS Alojado'),
        ('o', 'On Premise')
    )
    tecnologia = models.CharField(
        choices=TECNOLOGIA, max_length=1, blank=True, null=True)
    tipo = models.CharField(max_length=1, choices=TIPO, blank=True, null=True)
    ipGestion = models.CharField('IP de gestión', max_length=15)
    usuario = models.CharField('Usuario de acceso', max_length=50)
    passwd = models.CharField('Password de acceso', max_length=50)
    cliente = models.ForeignKey('clientes.Cliente', verbose_name=(
        "Clientes"), on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.hostname)


class Modulo(models.Model):
    """Definicón de los módulos de cada central"""
    nombre = models.CharField('Nombre del modulo', max_length=50)
    direccion = models.CharField('Direccion', max_length=50)
    poblacion = models.CharField('Poblacion', max_length=50)
    coordinador = models.CharField('Coordinador', max_length=50)
    telefCoord = models.CharField('Telefono coordinador', max_length=9)
    fullIp = models.BooleanField(default=True)
    TIPORED = (
        ('e', 'Estática'),
        ('d', 'Dinámica')
    )
    tipoRed = models.CharField(
        choices=TIPORED, max_length=1, blank=True, null=True)
    red = models.CharField('Red', max_length=20)
    vlan = models.CharField('Vlan de la red', max_length=50)
    observaciones = models.TextField()
    central = models.ForeignKey('clientes.Central', verbose_name=(
        "Modulos"), on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return str(self.nombre)
