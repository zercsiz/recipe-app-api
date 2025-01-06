from django.db import models
from django.contrib.auth.models import(
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.conf import settings



class UserManager(BaseUserManager):
    """Manager for user."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""

        if not email:
            raise ValueError('User must have an email address.')

        # extra_fields enables us to add new fields
        # without updating the create_user method
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)

        # self._db supports adding multiple databases if you chose to
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    objects = UserManager()



class Recipe(models.Model):
    """Recipe object."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.title