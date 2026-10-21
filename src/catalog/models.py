from django.core.exceptions import ValidationError
from django.db import models

from catalog.enums import ProductType, RelationshipType


class Product(models.Model):
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        db_index=True,
    )
    description = models.TextField(blank=True, default="")
    specs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Atributos técnicos (amperaje, polos, montaje, etc.)",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["sku"]

    def __str__(self):
        return f"[{self.get_product_type_display()}] {self.name} ({self.sku})"

    def get_compatible_components(self):
        """
        Retorna componentes principales (ej. interruptores) montables en este producto.
        """
        return (
            Product.objects.filter(
                inward_compatibilities__source=self,
                inward_compatibilities__relationship_type=RelationshipType.COMPATIBLE_WITH,
                is_active=True,
            )
            .distinct()
            .order_by("-inward_compatibilities__score", "name")
        )

    def get_accessories(self):
        """Retorna accesorios o complementos directos de este producto."""
        return (
            Product.objects.filter(
                inward_compatibilities__source=self,
                inward_compatibilities__relationship_type=RelationshipType.COMPLEMENT_OF,
                is_active=True,
            )
            .distinct()
            .order_by("-inward_compatibilities__score", "name")
        )


class ProductCompatibility(models.Model):
    source = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="outward_compatibilities",
        help_text="El producto anfitrión o principal (ej. Tablero o Interruptor)",
    )
    target = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inward_compatibilities",
        help_text="El producto compatible o accesorio a instalar",
    )
    relationship_type = models.CharField(
        max_length=30,
        choices=RelationshipType.choices,
        default=RelationshipType.COMPATIBLE_WITH,
        db_index=True,
    )
    score = models.PositiveIntegerField(
        default=100,
        help_text="Prioridad de recomendación (mayor valor = aparece primero)",
    )
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Compatibilidad entre Productos"
        verbose_name_plural = "Compatibilidades entre Productos"
        constraints = [
            # Evita duplicar exactamente la misma relación entre dos productos
            models.UniqueConstraint(
                fields=["source", "target", "relationship_type"],
                name="unique_source_target_rel_type",
            ),
            # Evita que un producto se relacione consigo mismo
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
        return f"{self.source.sku} ──[{self.relationship_type}]──▶ {self.target.sku}"

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.source_id and self.target_id and self.source_id == self.target_id:
            raise ValidationError("Un producto no puede ser compatible consigo mismo.")
