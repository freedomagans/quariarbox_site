from django.apps import AppConfig


# appconfig
class UserAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    # overriding method to call signals when needed
    def ready(self):
        import users.signals
