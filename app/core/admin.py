from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# This integrates with the django translation system
# if you change the language of django, everywhere there is
# a translation shortcut (_), it is gonna translate the text
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        # None is for title because we sant it to have no title
        (None, {'fields': ('email', 'password')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    exclude =['username']
    readonly_fields = ['last_login']
    add_fields = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser',

            )
        }),
    )

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe)