from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from catalog.enums import ProductType
from quotes.enums import QuoteStatus


def generate_next_folio() -> str:
    """Genera un folio secuencial con formato COT-YYYY-NNNN."""
    current_year = datetime.now().year
    prefix = f"COT-{current_year}-"
    last_quote = (
        Quote.objects.filter(folio__startswith=prefix).order_by("-folio").first()
    )
    if last_quote and last_quote.folio:
        try:
            last_seq = int(last_quote.folio.split("-")[-1])
            next_seq = last_seq + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1
    return f"{prefix}{next_seq:04d}"


class Quote(models.Model):
    folio = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        db_index=True,
        help_text="Folio secuencial de la cotización técnica (ej. COT-2026-0001)",
    )
    client_name = models.CharField(
        max_length=255,
        help_text="Nombre o razón social del cliente",
    )
    project_reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Referencia de obra o proyecto",
    )
    status = models.CharField(
        max_length=20,
        choices=QuoteStatus.choices,
        default=QuoteStatus.DRAFT,
        db_index=True,
        help_text="Estado actual en el ciclo de vida",
    )
    is_board_assembly = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indica si esta cotización corresponde a un ensamble de tablero",
    )
    board_product = models.ForeignKey(
        "catalog.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="board_quotes",
        help_text="Gabinete o tablero anfitrión si es ensamble de tablero",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_quotes",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Notas técnicas u observaciones",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cotización Técnica"
        verbose_name_plural = "Cotizaciones Técnicas"
        ordering = ["-created_at", "-folio"]

    def __str__(self):
        return f"[{self.folio}] {self.client_name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.folio:
            self.folio = generate_next_folio()
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if not self.folio:
            self.folio = generate_next_folio()
        if self.is_board_assembly:
            if not self.board_product:
                raise ValidationError(
                    {"board_product": ("Un ensamble requiere tablero anfitrión.")}
                )
            if self.board_product.product_type != ProductType.BOARD:
                raise ValidationError(
                    {
                        "board_product": (
                            "El producto anfitrión debe ser de tipo Tablero (BOARD)."
                        )
                    }
                )

    def can_edit(self) -> bool:
        """Determina si la cotización admite modificaciones de partidas."""
        return self.status in (QuoteStatus.DRAFT, QuoteStatus.VALIDATED)

    def is_validated(self) -> bool:
        """Determina si la cotización ha sido formalmente validada."""
        return self.status in (
            QuoteStatus.VALIDATED,
            QuoteStatus.SENT,
            QuoteStatus.ACCEPTED,
        )


class QuoteItem(models.Model):
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Cotización técnica contenedora",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="quote_items",
        help_text="Producto o componente del catálogo",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Cantidad de piezas (mínimo 1)",
    )
    slot_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Posición de ranura/circuito asignada en el tablero (opcional)",
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Notas técnicas de derivación o montaje",
    )

    class Meta:
        verbose_name = "Partida de Cotización"
        verbose_name_plural = "Partidas de Cotización"
        ordering = ["slot_position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["quote", "product", "slot_position"],
                name="unique_quote_product_slot",
            )
        ]

    def __str__(self):
        slot_repr = f" (Ranura {self.slot_position})" if self.slot_position else ""
        return f"{self.quantity}x {self.product.sku}{slot_repr}"

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.quantity < 1:
            raise ValidationError(
                {"quantity": "La cantidad mínima debe ser al menos 1."}
            )
        if self.quote_id and not self.quote.can_edit():
            raise ValidationError(
                "No se pueden modificar partidas en una cotización no editable."
            )
