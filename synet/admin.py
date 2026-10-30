from django.contrib import admin

# Register your models here.
# from .models import WaterConsumption, WaterCons, Persons, Counters, Paids, Fields, Receivers
from .models import Parametroi, WaterCons, Persons, Counters, Paids, Fields, Receivers, CashTransaction, TransactionType, TransactionCategory


# admin.site.register(WaterConsumption)
admin.site.register(WaterCons)
admin.site.register(Persons)
admin.site.register(Counters)
admin.site.register(Paids)
admin.site.register(Fields)
admin.site.register(Receivers)
admin.site.register(Parametroi)


@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'value', 'notes']
    search_fields = ['name']


@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'is_active', 'notes']
    list_filter = ['type', 'is_active']
    search_fields = ['name']


@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_date', 'category', 'type', 'amount', 'receiver']
    list_filter = ['category__type', 'transaction_date', 'receiver']
    search_fields = ['notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'transaction_date'