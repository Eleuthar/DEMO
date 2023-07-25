from django.apps import AppConfig


class UzrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'uzrz'

    def ready(self):
        import uzr.signals
