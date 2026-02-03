from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'autodis_compras.apps.notifications'
    verbose_name = 'Notificaciones'

    def ready(self):
        import autodis_compras.apps.notifications.signals  # noqa: F401
