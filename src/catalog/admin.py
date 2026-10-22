"""Panel de administración para el catálogo eléctrico y compatibilidades."""

from django.contrib import admin

from catalog.models import Product, ProductCompatibility


class ProductCompatibilityInline(admin.TabularInline):
    model = ProductCompatibility
    fk_name = "source"
    extra = 1
    autocomplete_fields = ["target"]
    fields = ["target", "relationship_type", "score", "notes"]
    verbose_name = "Compatibilidad saliente"
    verbose_name_plural = "Compatibilidades entre Productos"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "nombre_corto",
        "nombre_largo",
        "is_active",
        "updated_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["nombre_corto", "nombre_largo", "descripcion"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductCompatibilityInline]
    fieldsets = (
        (
            "Identificación del Producto",
            {
                "fields": ("nombre_corto", "nombre_largo", "is_active"),
            },
        ),
        (
            "Descripción y Ficha Técnica",
            {
                "fields": ("descripcion",),
            },
        ),
        (
            "Auditoría",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ProductCompatibility)
class ProductCompatibilityAdmin(admin.ModelAdmin):
    list_display = [
        "source",
        "relationship_type",
        "target",
        "score",
        "notes",
    ]
    list_filter = ["relationship_type"]
    search_fields = [
        "source__nombre_corto",
        "source__nombre_largo",
        "target__nombre_corto",
        "target__nombre_largo",
    ]
    autocomplete_fields = ["source", "target"]
