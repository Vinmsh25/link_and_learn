from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Bank, CreditTransaction, Session, SessionTimer, Review


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'credits', 'is_online', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_online')
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'credits', 'availability')}),
        ('Status', {'fields': ('is_online', 'last_seen', 'last_support_request')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('total_credits', 'updated_at')


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'balance_after', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__email', 'user__name', 'description')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'is_active', 'start_time', 'end_time')
    list_filter = ('is_active', 'start_time')


@admin.register(SessionTimer)
class SessionTimerAdmin(admin.ModelAdmin):
    list_display = ('session', 'teacher', 'start_time', 'end_time', 'duration_seconds')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewee', 'rating', 'session', 'created_at')
    list_filter = ('rating', 'created_at')
