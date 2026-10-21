from django.contrib import admin

from catalog.models import Product, ProductCompatibility


class ProductCompatibilityInline(admin.TabularInline):
    model = ProductCompatibility
    fk_name = "source"
    extra = 1
    autocomplete_fields = ["target"]
    fields = ["target", "relationship_type", "score", "notes"]
    verbose_name = "Compatibilidad saliente"
    verbose_name_plural = "Compatibilidades entre Productos (Componentes / Accesorios)"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "sku",
        "name",
        "product_type",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["product_type", "is_active"]
    search_fields = ["sku", "name", "description"]
    prepopulated_fields = {"slug": ("sku",)}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ProductCompatibilityInline]
    fieldsets = (
        (
            "Identificación Principal",
            {
                "fields": ("sku", "name", "slug", "product_type", "is_active"),
            },
        ),
        (
            "Detalle Técnico",
            {
                "fields": ("description", "specs"),
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
        "source__sku",
        "source__name",
        "target__sku",
        "target__name",
    ]
    autocomplete_fields = ["source", "target"]
