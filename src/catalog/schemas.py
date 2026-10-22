"""Esquemas Pydantic v2 para la API REST del catálogo de compatibilidades."""

from typing import Optional

from ninja import Schema


class ProductSchema(Schema):
    id: int
    nombre_corto: str
    nombre_largo: str
    descripcion: str = ""
    is_active: bool = True
    category: Optional[str] = ""
    notes: Optional[str] = ""


class ProductListResponse(Schema):
    total: int
    items: list[ProductSchema]


class CompatibilityEdgeSchema(Schema):
    id: int
    target_id: int
    target_nombre_corto: str
    target_nombre_largo: str
    relationship_type: str
    score: int
    notes: str = ""


class ProductCompatibilitiesResponse(Schema):
    product: ProductSchema
    compatibilities: list[CompatibilityEdgeSchema]


class ProductTreeResponse(Schema):
    product: ProductSchema
    compatible_components: list[ProductSchema] = []
    required_accessories: list[ProductSchema] = []
    complements: list[ProductSchema] = []
    alternatives: list[ProductSchema] = []
    host_equipment: list[ProductSchema] = []
    used_in_equipment: list[ProductSchema] = []
    alternative_for: list[ProductSchema] = []
