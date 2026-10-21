from typing import Any, Dict, List, Optional

from ninja import Schema


class ProductSchema(Schema):
    id: int
    sku: str
    name: str
    slug: str
    product_type: str
    description: Optional[str] = ""
    specs: Dict[str, Any] = {}
    is_active: bool


class ProductListResponse(Schema):
    count: int
    items: List[ProductSchema]


class CompatibilityEdgeSchema(Schema):
    target_sku: str
    target_name: str
    target_type: str
    relationship_type: str
    score: int
    notes: Optional[str] = ""
    specs: Dict[str, Any] = {}


class ProductHeaderSchema(Schema):
    sku: str
    name: str


class ProductCompatibilitiesResponse(Schema):
    product: ProductHeaderSchema
    compatibilities: List[CompatibilityEdgeSchema]


class NestedAccessorySchema(Schema):
    id: int
    sku: str
    name: str
    product_type: str
    relationship_type: str
    score: int
    notes: Optional[str] = ""
    specs: Dict[str, Any] = {}


class NestedComponentSchema(Schema):
    id: int
    sku: str
    name: str
    product_type: str
    relationship_type: str
    score: int
    notes: Optional[str] = ""
    specs: Dict[str, Any] = {}
    accessories: List[NestedAccessorySchema] = []


class ProductTreeResponse(Schema):
    id: int
    sku: str
    name: str
    product_type: str
    specs: Dict[str, Any] = {}
    compatible_components: List[NestedComponentSchema] = []
    direct_accessories: List[NestedAccessorySchema] = []
