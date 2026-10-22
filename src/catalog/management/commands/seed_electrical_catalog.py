"""Comando de gestión para sembrar datos iniciales de catálogo y compatibilidades."""

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.enums import RelationshipType
from catalog.models import Product, ProductCompatibility


class Command(BaseCommand):
    help = (
        "Carga datos semilla representativos del catálogo eléctrico "
        "y grafo de compatibilidades"
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Cargando catálogo eléctrico semilla...")

        # 1. Crear productos (Nodos)
        products_data = [
            {
                "nombre_corto": "NQ-225-30P",
                "nombre_largo": "Tablero de Alumbrado NQ 225A 30 Polos",
                "descripcion": (
                    "Tablero de alumbrado tipo NQ para interruptores "
                    "derivados enchufables QO o atornillables QOB."
                ),
                "is_active": True,
            },
            {
                "nombre_corto": "QO-120",
                "nombre_largo": "Interruptor Termomagnético QO 1 Polo 20A",
                "descripcion": (
                    "Interruptor automático miniatura termomagnético "
                    "enchufable de 1 polo 20A 120/240V."
                ),
                "is_active": True,
            },
            {
                "nombre_corto": "QO-230",
                "nombre_largo": "Interruptor Termomagnético QO 2 Polos 30A",
                "descripcion": (
                    "Interruptor automático miniatura termomagnético "
                    "enchufable de 2 polos 30A 120/240V."
                ),
                "is_active": True,
            },
            {
                "nombre_corto": "EDB-3100",
                "nombre_largo": "Interruptor Termomagnético EDB 3 Polos 100A",
                "descripcion": (
                    "Interruptor de caja moldeada tipo marco E "
                    "de 3 polos 100A 480Y/277V."
                ),
                "is_active": True,
            },
            {
                "nombre_corto": "AUX-QO",
                "nombre_largo": "Contacto Auxiliar 1NA/1NC para QO",
                "descripcion": (
                    "Módulo de contacto auxiliar para señalización "
                    "de estado de apertura/cierre en interruptores QO."
                ),
                "is_active": True,
            },
            {
                "nombre_corto": "KIT-ZAP-225",
                "nombre_largo": "Kit Zapata Neutro 225A Aluminio",
                "descripcion": (
                    "Juego de zapatas mecánicas principales de "
                    "aluminio para tableros NQ hasta 225A."
                ),
                "is_active": True,
            },
            {
                "nombre_corto": "QOB-120",
                "nombre_largo": "Interruptor QOB 1 Polo 20A Atornillable",
                "descripcion": (
                    "Alternativa atornillable para montaje en tableros NQ."
                ),
                "is_active": True,
            },
        ]

        products_by_short = {}
        for p_data in products_data:
            p, created = Product.objects.update_or_create(
                nombre_corto=p_data["nombre_corto"],
                defaults={
                    "nombre_largo": p_data["nombre_largo"],
                    "descripcion": p_data["descripcion"],
                    "is_active": p_data["is_active"],
                },
            )
            products_by_short[p.nombre_corto] = p
            status = "creado" if created else "actualizado"
            self.stdout.write(f"  - Producto {p.nombre_corto} (ID {p.id}) {status}")

        # 2. Crear relaciones dirigidas (Aristas)
        compatibilities_data = [
            # NQ aloja QO-120 y QO-230
            {
                "source": "NQ-225-30P",
                "target": "QO-120",
                "type": RelationshipType.COMPATIBLE_WITH,
                "score": 100,
                "notes": "Montaje enchufable compatible en barra NQ",
            },
            {
                "source": "NQ-225-30P",
                "target": "QO-230",
                "type": RelationshipType.COMPATIBLE_WITH,
                "score": 95,
                "notes": "Montaje enchufable bifásico en barra NQ",
            },
            {
                "source": "NQ-225-30P",
                "target": "QOB-120",
                "type": RelationshipType.COMPATIBLE_WITH,
                "score": 90,
                "notes": "Montaje atornillable compatible en barra NQ",
            },
            # NQ recomienda zapata KIT-ZAP-225
            {
                "source": "NQ-225-30P",
                "target": "KIT-ZAP-225",
                "type": RelationshipType.COMPLEMENT_OF,
                "score": 90,
                "notes": "Accesorio complementario recomendado de acometida",
            },
            # QO-120 puede llevar contacto auxiliar
            {
                "source": "QO-120",
                "target": "AUX-QO",
                "type": RelationshipType.COMPLEMENT_OF,
                "score": 100,
                "notes": "Accesorio de señalización para contacto auxiliar",
            },
            # QOB-120 es alternativa de QO-120
            {
                "source": "QO-120",
                "target": "QOB-120",
                "type": RelationshipType.ALTERNATIVE_TO,
                "score": 85,
                "notes": "Reemplazo de montaje atornillable",
            },
        ]

        for c_data in compatibilities_data:
            source = products_by_short[c_data["source"]]
            target = products_by_short[c_data["target"]]
            edge, created = ProductCompatibility.objects.update_or_create(
                source=source,
                target=target,
                relationship_type=c_data["type"],
                defaults={
                    "score": c_data["score"],
                    "notes": c_data["notes"],
                },
            )
            action = "creada" if created else "actualizada"
            self.stdout.write(
                f"  - Relación {source.nombre_corto} -> {target.nombre_corto} "
                f"({c_data['type']}) {action}"
            )

        self.stdout.write(self.style.SUCCESS("Catálogo sembrado exitosamente."))
