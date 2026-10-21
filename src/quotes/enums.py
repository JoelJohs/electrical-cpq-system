from django.db import models


class QuoteStatus(models.TextChoices):
    DRAFT = "DRAFT", "Borrador (Editable)"
    VALIDATED = "VALIDATED", "Validada Técnicamente"
    SENT = "SENT", "Emitida al Cliente (Solo Lectura)"
    ACCEPTED = "ACCEPTED", "Aceptada / En Taller (Solo Lectura)"
    CANCELLED = "CANCELLED", "Cancelada (Solo Lectura)"
