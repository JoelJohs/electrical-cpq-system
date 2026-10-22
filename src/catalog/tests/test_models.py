from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from catalog.enums import RelationshipType
from catalog.models import Product, ProductCompatibility


class ProductModelTest(TestCase):
    def setUp(self):
        self.tablero = Product.objects.create(
            nombre_corto="NQ-225",
            nombre_largo="Tablero Alumbrado NQ 225A 30 Polos",
            descripcion="Tablero de alumbrado tipo NQ",
            is_active=True,
        )
        self.interruptor = Product.objects.create(
            nombre_corto="QO-120",
            nombre_largo="Interruptor Termomagnético QO 1P 20A",
            descripcion="Interruptor miniatura enchufable 1P 20A",
            is_active=True,
        )
        self.accesorio = Product.objects.create(
            nombre_corto="AUX-QO",
            nombre_largo="Contacto Auxiliar 1NA/1NC para QO",
            descripcion="Contacto auxiliar de señalización",
            is_active=True,
        )

    def test_product_str_representation(self):
        self.assertIn("NQ-225", str(self.tablero))
        self.assertIn("Tablero", str(self.tablero))

    def test_create_valid_compatibility(self):
        compat = ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
            score=100,
            notes="Hasta 30 circuitos",
        )
        self.assertEqual(compat.source, self.tablero)
        self.assertEqual(compat.target, self.interruptor)
        self.assertEqual(compat.relationship_type, RelationshipType.COMPATIBLE_WITH)

    def test_prevent_self_relation_validation_error(self):
        compat = ProductCompatibility(
            source=self.tablero,
            target=self.tablero,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        with self.assertRaises(ValidationError):
            compat.full_clean()

    def test_prevent_self_relation_integrity_error(self):
        with self.assertRaises(IntegrityError):
            ProductCompatibility.objects.bulk_create(
                [
                    ProductCompatibility(
                        source=self.tablero,
                        target=self.tablero,
                        relationship_type=RelationshipType.COMPATIBLE_WITH,
                    )
                ]
            )

    def test_prevent_duplicate_relation_integrity_error(self):
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        with self.assertRaises(IntegrityError):
            ProductCompatibility.objects.create(
                source=self.tablero,
                target=self.interruptor,
                relationship_type=RelationshipType.COMPATIBLE_WITH,
            )

    def test_allow_different_relationship_types_between_same_products(self):
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        compat_alt = ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.REQUIRES,
        )
        self.assertIsNotNone(compat_alt.pk)

    def test_get_compatible_items(self):
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        components = list(self.tablero.get_compatible_items())
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0].nombre_corto, "QO-120")

    def test_get_complements(self):
        ProductCompatibility.objects.create(
            source=self.interruptor,
            target=self.accesorio,
            relationship_type=RelationshipType.COMPLEMENT_OF,
        )
        accessories = list(self.interruptor.get_complements())
        self.assertEqual(len(accessories), 1)
        self.assertEqual(accessories[0].nombre_corto, "AUX-QO")

    def test_directedness_does_not_return_inverse_relationship(self):
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        self.assertNotIn(self.tablero, self.interruptor.get_compatible_items())
        self.assertNotIn(self.tablero, self.interruptor.get_complements())

    def test_inactive_products_are_excluded_from_compatibilities(self):
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        self.interruptor.is_active = False
        self.interruptor.save()

        components = list(self.tablero.get_compatible_items())
        self.assertEqual(len(components), 0)
