from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Create your models here.


class Usuario(AbstractUser):
    """Modelo de usuario
    Heredamos de AbstractUser, cambiamos el campo username con email y añadimos algunos campos extra
    """

    email = models.EmailField(
        'email address',
        unique=True,
        error_messages={'unique': 'Un usuario ya existe con este email'}
    )
    tfno_regex = RegexValidator(
        regex=r'\+?1?\d{9,11}$',
        message="Telefono en el formato +99999999999, hasta 11 digitos"
    )
    numero_telefono = models.CharField(
        validators=[tfno_regex], max_length=11, blank=True)
    verificado = models.BooleanField(
        'verificado',
        default=True,
        help_text='Configurado a True cuando el usuario ha verificado su email'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return(self.username)
