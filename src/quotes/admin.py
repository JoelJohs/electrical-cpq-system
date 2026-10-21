"""Configuración del panel de administración para cotizaciones técnicas (CPQ)."""

from django.contrib import admin

from quotes.models import Quote, QuoteItem


class QuoteItemInline(admin.TabularInline):
    """Inline tabular para partidas de cotización y componentes de tablero."""

    model = QuoteItem
    extra = 0
    autocomplete_fields = ["product"]
    fields = ["product", "quantity", "slot_position", "notes"]
    verbose_name = "Partida"
    verbose_name_plural = "Partidas / Componentes Instalados"


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Administrador corporativo para cotizaciones técnicas y ensambles."""

    list_display = [
        "folio",
        "client_name",
        "project_reference",
        "status",
        "is_board_assembly",
        "board_product",
        "created_at",
    ]
    list_filter = ["status", "is_board_assembly", "created_at"]
    search_fields = ["folio", "client_name", "project_reference"]
    readonly_fields = ["folio", "created_at", "updated_at"]
    autocomplete_fields = ["board_product"]
    inlines = [QuoteItemInline]
    fieldsets = (
        (
            "Identificación y Estado",
            {
                "fields": (
                    "folio",
                    "client_name",
                    "project_reference",
                    "status",
                ),
            },
        ),
        (
            "Configuración de Ensamble de Tablero",
            {
                "fields": (
                    "is_board_assembly",
                    "board_product",
                ),
            },
        ),
        (
            "Notas de Ingeniería",
            {
                "fields": ("notes",),
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


@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    """Administrador individual para partidas."""

    list_display = [
        "quote",
        "product",
        "quantity",
        "slot_position",
    ]
    list_filter = ["quote__status", "product__product_type"]
    search_fields = ["quote__folio", "product__sku", "product__name"]
    autocomplete_fields = ["quote", "product"]
