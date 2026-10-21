from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.enums import ProductType, RelationshipType
from catalog.models import Product, ProductCompatibility


class Command(BaseCommand):
    help = (
        "Carga datos semilla representativos del catálogo eléctrico "
        "y grafo de compatibilidades"
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Cargando catálogo eléctrico semilla...")

        # 1. Crear o actualizar Nodos (Productos)
        products_data = [
            {
                "sku": "TAB-NQ-225",
                "name": "Tablero Alumbrado NQ 225A 30 Polos",
                "slug": "tab-nq-225",
                "product_type": ProductType.BOARD,
                "description": (
                    "Tablero de alumbrado tipo NQ para interruptores "
                    "derivados enchufables QO o atornillables QOB."
                ),
                "specs": {
                    "espacios": 30,
                    "amperaje_max": 225,
                    "fases": 3,
                    "voltaje_max": 240,
                },
                "is_active": True,
            },
            {
                "sku": "INT-QO-120",
                "name": "Interruptor Termomagnético QO 1P 20A",
                "slug": "int-qo-120",
                "product_type": ProductType.COMPONENT,
                "description": (
                    "Interruptor automático miniatura termomagnético "
                    "enchufable de 1 polo 20A 120/240V."
                ),
                "specs": {
                    "polos": 1,
                    "amperaje": 20,
                    "montaje": "enchufable",
                    "ic_ka": 10,
                },
                "is_active": True,
            },
            {
                "sku": "INT-EDB-3100",
                "name": "Interruptor Termomagnético EDB 3P 100A",
                "slug": "int-edb-3100",
                "product_type": ProductType.COMPONENT,
                "description": (
                    "Interruptor de caja moldeada tipo marco E "
                    "de 3 polos 100A 480Y/277V."
                ),
                "specs": {
                    "polos": 3,
                    "amperaje": 100,
                    "montaje": "atornillable",
                    "ic_ka": 18,
                },
                "is_active": True,
            },
            {
                "sku": "ACC-AUX-QO",
                "name": "Contacto Auxiliar 1NA/1NC para QO",
                "slug": "acc-aux-qo",
                "product_type": ProductType.ACCESSORY,
                "description": (
                    "Módulo de contacto auxiliar para señalización "
                    "de estado de apertura/cierre en interruptores QO."
                ),
                "specs": {
                    "tipo_contacto": "1NA/1NC",
                    "voltaje_control": "120V",
                    "montaje": "lateral",
                },
                "is_active": True,
            },
            {
                "sku": "KIT-ZAP-225",
                "name": "Kit Zapata Neutro 225A Aluminio",
                "slug": "kit-zap-225",
                "product_type": ProductType.ACCESSORY,
                "description": (
                    "Juego de zapatas mecánicas principales de "
                    "aluminio para tableros NQ hasta 225A."
                ),
                "specs": {
                    "material": "aluminio",
                    "calibre": "4-300 kcmil",
                    "amperaje": 225,
                },
                "is_active": True,
            },
        ]

        products_by_sku = {}
        for pdata in products_data:
            prod, created = Product.objects.update_or_create(
                sku=pdata["sku"],
                defaults=pdata,
            )
            products_by_sku[prod.sku] = prod
            action = "Creado" if created else "Actualizado"
            self.stdout.write(f"  · {action} producto: {prod.sku} ({prod.name})")

        # 2. Crear Aristas Dirigidas de Compatibilidad
        compatibilities_data = [
            # Tablero NQ aloja Interruptor QO 20A
            {
                "source": products_by_sku["TAB-NQ-225"],
                "target": products_by_sku["INT-QO-120"],
                "relationship_type": RelationshipType.COMPATIBLE_WITH,
                "score": 100,
                "notes": "Hasta 30 circuitos en total",
            },
            # Tablero NQ complementa con Kit Zapata
            {
                "source": products_by_sku["TAB-NQ-225"],
                "target": products_by_sku["KIT-ZAP-225"],
                "relationship_type": RelationshipType.COMPLEMENT_OF,
                "score": 90,
                "notes": "Opcional para barras de neutro / tierra",
            },
            # Interruptor QO recibe Contacto Auxiliar
            {
                "source": products_by_sku["INT-QO-120"],
                "target": products_by_sku["ACC-AUX-QO"],
                "relationship_type": RelationshipType.COMPLEMENT_OF,
                "score": 100,
                "notes": "Montaje lateral izquierdo en interruptor QO",
            },
        ]

        for cdata in compatibilities_data:
            compat, created = ProductCompatibility.objects.update_or_create(
                source=cdata["source"],
                target=cdata["target"],
                relationship_type=cdata["relationship_type"],
                defaults={
                    "score": cdata["score"],
                    "notes": cdata["notes"],
                },
            )
            action = "Creada" if created else "Actualizada"
            edge_repr = (
                f"{compat.source.sku} ──[{compat.relationship_type}]──▶ "
                f"{compat.target.sku}"
            )
            self.stdout.write(f"  · {action} compatibilidad: {edge_repr}")

        self.stdout.write(
            self.style.SUCCESS("✓ Catálogo semilla cargado exitosamente.")
        )
