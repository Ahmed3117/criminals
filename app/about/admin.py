from django.contrib import admin
from .models import Criminal
from django.utils.html import format_html
@admin.register(Criminal)
class CriminalAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_image', 'is_criminal', 'danger_marker')
    search_fields = ('name',)
    list_filter = ('is_criminal',)

    def display_image(self, obj):
        """Display the image in the admin list view."""
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: auto;"/>', obj.image.url)
        return "No Image"

    display_image.short_description = 'Image'

    def danger_marker(self, obj):
        """Mark as danger if is_criminal is True."""
        if obj.is_criminal:
            return format_html('<span style="color: red; font-weight: bold;">Danger</span>')
        return "Safe"

    danger_marker.short_description = 'Status'