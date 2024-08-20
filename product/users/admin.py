from django.contrib import admin
from .models import CustomUser, Balance, Subscription


class BalanceInline(admin.StackedInline):
    model = Balance
    can_delete = False
    verbose_name = 'Баланс'
    verbose_name_plural = 'Баланс'

class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 1


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    inlines = [BalanceInline, SubscriptionInline]
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username')
    ordering = ('-id',)
    filter_horizontal = ()

admin.site.register(Balance)
admin.site.register(Subscription)
