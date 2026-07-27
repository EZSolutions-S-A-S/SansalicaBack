from django.contrib import admin

from .models import InmuebleModel, InmueblePhotoModel


class InmueblePhotoInline(admin.TabularInline):
    model = InmueblePhotoModel
    extra = 1


@admin.register(InmuebleModel)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ['title', 'operation_type', 'property_type', 'price', 'status', 'featured', 'created_at']
    list_filter = ['operation_type', 'property_type', 'status', 'featured']
    search_fields = ['title', 'location', 'description']
    inlines = [InmueblePhotoInline]
