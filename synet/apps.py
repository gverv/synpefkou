from django.apps import AppConfig


class SynetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'synet'

    def ready(self):
        from auditlog.registry import auditlog

        from .models import (
            CashTransaction,
            Counters,
            Fields,
            Paids,
            Parametroi,
            Persons,
            Receivers,
            TransactionCategory,
            TransactionType,
            WaterCons,
            Ydronomeas,
        )

        for model in (
            Persons,
            Counters,
            Receivers,
            Fields,
            Ydronomeas,
            WaterCons,
            Paids,
            Parametroi,
            TransactionType,
            TransactionCategory,
            CashTransaction,
        ):
            auditlog.register(model)
