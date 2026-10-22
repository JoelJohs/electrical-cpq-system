"""Modelos del catálogo y grafo de compatibilidades eléctricas."""

from django.core.exceptions import ValidationError
from django.db import models

from catalog.enums import RelationshipType


class Product(models.Model):
    """Producto o componente del catálogo técnico."""

    nombre_corto = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Código o identificador corto (ej. NQ-225, QO-120)",
    )
    nombre_largo = models.CharField(
        max_length=255,
        help_text="Nombre descriptivo completo comercial",
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        help_text="Descripción o especificaciones técnicas del producto",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Determina si el producto está vigente en catálogo",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre_corto"]

    def __str__(self):
        return f"{self.nombre_corto} - {self.nombre_largo}"

    def get_compatible_items(self):
        """Retorna productos compatibles salientes de este producto."""
        return (
            Product.objects.filter(
                inward_compatibilities__source=self,
                inward_compatibilities__relationship_type=RelationshipType.COMPATIBLE_WITH,
                is_active=True,
            )
            .distinct()
            .order_by("-inward_compatibilities__score", "nombre_corto")
        )

    def get_required_accessories(self):
        """Retorna accesorios mandatorios que este producto requiere."""
        return (
            Product.objects.filter(
                inward_compatibilities__source=self,
                inward_compatibilities__relationship_type=RelationshipType.REQUIRES,
                is_active=True,
            )
            .distinct()
            .order_by("-inward_compatibilities__score", "nombre_corto")
        )

    def get_complements(self):
        """Retorna accesorios sugeridos o complementos no obligatorios."""
        return (
            Product.objects.filter(
                inward_compatibilities__source=self,
                inward_compatibilities__relationship_type=RelationshipType.COMPLEMENT_OF,
                is_active=True,
            )
            .distinct()
            .order_by("-inward_compatibilities__score", "nombre_corto")
        )

    def get_alternatives(self):
        """Retorna sustitutos o reemplazos directos."""
        return (
            Product.objects.filter(
                inward_compatibilities__source=self,
                inward_compatibilities__relationship_type=RelationshipType.ALTERNATIVE_TO,
                is_active=True,
            )
            .distinct()
            .order_by("-inward_compatibilities__score", "nombre_corto")
        )


class ProductCompatibility(models.Model):
    """Arista dirigida de compatibilidad entre dos productos."""

    source = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="outward_compatibilities",
        help_text="Producto anfitrión o base",
    )
    target = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inward_compatibilities",
        help_text="Producto compatible, accesorio o alternativa",
    )
    relationship_type = models.CharField(
        max_length=30,
        choices=RelationshipType.choices,
        default=RelationshipType.COMPATIBLE_WITH,
        db_index=True,
    )
    score = models.PositiveIntegerField(
        default=100,
        help_text="Prioridad de recomendación (mayor valor = mayor relevancia)",
    )
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Compatibilidad entre Productos"
        verbose_name_plural = "Compatibilidades entre Productos"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "target", "relationship_type"],
                name="unique_source_target_rel_type",
            ),
            models.CheckConstraint(
                condition=~models.Q(source=models.F("target")),
                name="prevent_self_relation",
                violation_error_message=(
                    "Un producto no puede ser compatible consigo mismo."
                ),
            ),
        ]
        indexes = [
            models.Index(
                fields=["source", "relationship_type"],
                name="catalog_compat_src_rel_idx",
            ),
            models.Index(
                fields=["target", "relationship_type"],
                name="catalog_compat_tgt_rel_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.source.nombre_corto} ──[{self.relationship_type}]──▶ "
            f"{self.target.nombre_corto}"
        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.source_id and self.target_id and self.source_id == self.target_id:
            raise ValidationError("Un producto no puede ser compatible consigo mismo.")
