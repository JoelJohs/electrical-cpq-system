"""Esquemas Pydantic v2 para la API REST del configurador de cotizaciones."""

from datetime import datetime
from typing import Any, Optional

from ninja import Schema
from pydantic import Field


class CreateQuoteSchema(Schema):
    client_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Nombre o razón social del cliente",
    )
    project_reference: str = Field(
        "",
        max_length=255,
        description="Referencia de obra o proyecto",
    )
    is_board_assembly: bool = Field(
        False,
        description="Indica si es un ensamble de tablero técnico",
    )
    board_sku: Optional[str] = Field(
        None,
        description="SKU del tablero anfitrión si is_board_assembly=True",
    )
    notes: str = Field("", description="Notas técnicas o de ingeniería")


class AddQuoteItemSchema(Schema):
    product_sku: str = Field(..., description="SKU del producto a agregar")
    quantity: int = Field(
        1, ge=1, description="Cantidad a agregar (debe ser mayor a 0)"
    )
    slot_position: Optional[int] = Field(
        None,
        ge=1,
        description="Posición física de ranura/espacio en tablero",
    )
    notes: str = Field("", max_length=255, description="Notas de la partida")


class UpdateQuoteItemSchema(Schema):
    quantity: Optional[int] = Field(None, ge=1, description="Nueva cantidad")
    slot_position: Optional[int] = Field(
        None, ge=1, description="Nueva posición física en tablero"
    )
    notes: Optional[str] = Field(
        None, max_length=255, description="Notas de la partida"
    )


class QuoteItemDetailSchema(Schema):
    id: int
    product_sku: str
    product_name: str
    product_type: str
    quantity: int
    slot_position: Optional[int] = None
    notes: str = ""
    specs: dict[str, Any] = {}


class QuoteDetailSchema(Schema):
    id: int
    folio: str
    client_name: str
    project_reference: str
    status: str
    is_board_assembly: bool
    board_sku: Optional[str] = None
    board_name: Optional[str] = None
    items_count: int
    notes: str
    created_at: datetime
    items: list[QuoteItemDetailSchema] = []


class ValidationErrorDetailSchema(Schema):
    code: str
    message: str
    details: dict[str, Any] = {}


class ValidationSummarySchema(Schema):
    total_slots_capacity: int
    occupied_slots: int
    available_slots: int
    total_items: int


class ValidationResultSchema(Schema):
    valid: bool
    errors: list[ValidationErrorDetailSchema] = []
    warnings: list[dict[str, Any]] = []
    summary: ValidationSummarySchema
    suggested_accessories: list[dict[str, Any]] = []


class BOMItemSchema(Schema):
    item_id: Optional[int] = None
    sku: str
    name: str
    product_type: str
    quantity: int
    slot_position: Optional[int] = None
    notes: str = ""
    specs: Optional[dict[str, Any]] = None


class AggregatedMaterialSchema(Schema):
    sku: str
    name: str
    product_type: str
    total_quantity: int


class BOMResponseSchema(Schema):
    folio: str
    client_name: str
    project_reference: str
    is_board_assembly: bool
    status: str
    board: Optional[dict[str, Any]] = None
    items: list[BOMItemSchema] = []
    aggregated_materials: list[AggregatedMaterialSchema] = []
    total_components_count: int
    created_at: Optional[str] = None


class TransitionStatusSchema(Schema):
    target_status: str = Field(
        ...,
        description="Nuevo estado objetivo para la cotización",
    )
    reason: Optional[str] = Field(
        "",
        description="Motivo o justificación del cambio de estado",
    )
