from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from catalog.enums import ProductType, RelationshipType
from catalog.models import Product, ProductCompatibility


class ProductModelTest(TestCase):
    def setUp(self):
        self.tablero = Product.objects.create(
            sku="TAB-NQ-225",
            name="Tablero Alumbrado NQ 225A 30 Polos",
            slug="tab-nq-225",
            product_type=ProductType.BOARD,
            specs={"espacios": 30, "amperaje_max": 225, "fases": 3},
            is_active=True,
        )
        self.interruptor = Product.objects.create(
            sku="INT-QO-120",
            name="Interruptor Termomagnético QO 1P 20A",
            slug="int-qo-120",
            product_type=ProductType.COMPONENT,
            specs={"polos": 1, "amperaje": 20, "montaje": "enchufable"},
            is_active=True,
        )
        self.accesorio = Product.objects.create(
            sku="ACC-AUX-QO",
            name="Contacto Auxiliar 1NA/1NC para QO",
            slug="acc-aux-qo",
            product_type=ProductType.ACCESSORY,
            specs={"tipo_contacto": "1NA/1NC", "voltaje_control": "120V"},
            is_active=True,
        )

    def test_product_str_representation(self):
        self.assertIn("TAB-NQ-225", str(self.tablero))
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
        # bulk_create no ejecuta save() ni clean(), probando directamente
        # el CheckConstraint de la BD
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

    def test_get_compatible_components(self):
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        components = list(self.tablero.get_compatible_components())
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0].sku, "INT-QO-120")

    def test_get_accessories(self):
        ProductCompatibility.objects.create(
            source=self.interruptor,
            target=self.accesorio,
            relationship_type=RelationshipType.COMPLEMENT_OF,
        )
        accessories = list(self.interruptor.get_accessories())
        self.assertEqual(len(accessories), 1)
        self.assertEqual(accessories[0].sku, "ACC-AUX-QO")

    def test_directedness_does_not_return_inverse_relationship(self):
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        # El interruptor no debe devolver el tablero como accesorio o componente
        self.assertNotIn(self.tablero, self.interruptor.get_compatible_components())
        self.assertNotIn(self.tablero, self.interruptor.get_accessories())

    def test_inactive_products_are_excluded_from_compatibilities(self):
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        self.interruptor.is_active = False
        self.interruptor.save()

        components = list(self.tablero.get_compatible_components())
        self.assertEqual(len(components), 0)
