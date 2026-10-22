"""Rutas web para la aplicación de catálogo y exploración de compatibilidades."""

from django.urls import path

from catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.explorer_view, name="explorer"),
    path(
        "api/products/<int:product_id>/tree/",
        views.product_tree_json_view,
        name="product_tree_json",
    ),
]
