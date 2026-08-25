from django.contrib import admin

from .models import InmuebleModel, InmueblePhotoModel


class InmueblePhotoInline(admin.TabularInline):
    model = InmueblePhotoModel
    extra = 1
    fields = ['image', 'order']
    ordering = ['order', 'id']


@admin.register(InmuebleModel)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ['title', 'operation_type', 'property_type', 'price', 'status', 'featured', 'created_at']
    list_filter = ['operation_type', 'property_type', 'status', 'featured']
    search_fields = ['title', 'location', 'description']
    list_editable = ['status', 'featured']
    ordering = ['-created_at']
    inlines = [InmueblePhotoInline]
    fieldsets = [
        ('Información general', {
            'fields': ['title', 'operation_type', 'property_type', 'price', 'location', 'description'],
        }),
        ('Características físicas', {
            'fields': ['square_meters', 'floor', 'bedrooms', 'bathrooms', 'parking_spots'],
        }),
        ('Features y amenities', {
            'fields': ['features', 'amenities'],
        }),
        ('Estado y visibilidad', {
            'fields': ['status', 'featured'],
        }),
    ]