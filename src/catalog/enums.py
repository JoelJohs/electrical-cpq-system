from django.db import models


class ProductType(models.TextChoices):
    BOARD = "BOARD", "Tablero / Gabinete"
    COMPONENT = "COMPONENT", "Componente Principal (Interruptor, Módulo)"
    ACCESSORY = "ACCESSORY", "Accesorio / Complemento"


class RelationshipType(models.TextChoices):
    COMPATIBLE_WITH = "COMPATIBLE_WITH", "Compatible dentro de (Montaje principal)"
    COMPLEMENT_OF = "COMPLEMENT_OF", "Complemento o Accesorio de"
    REQUIRES = "REQUIRES", "Requiere obligatoriamente"
    ALTERNATIVE_TO = "ALTERNATIVE_TO", "Alternativa / Reemplazo directo"
