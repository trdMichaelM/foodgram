from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_ROLES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    role = models.CharField(
        _('custom roles'),
        max_length=16,
        choices=USER_ROLES,
        default='user'
    )
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    email = models.EmailField(_('email address'), max_length=254)

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    class Meta:
        ordering = ['pk']
