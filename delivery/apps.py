from django.apps import AppConfig


class DeliveryAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'delivery'

    def ready(self):
        import delivery.signals