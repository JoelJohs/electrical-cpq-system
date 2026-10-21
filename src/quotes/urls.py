"""Rutas web para las interfaces de cotizaciones técnicas y configurador."""

from django.urls import path

from quotes import views

app_name = "quotes"

urlpatterns = [
    path("", views.quote_list_view, name="quote_list"),
    path("new/", views.quick_quote_view, name="quick_quote"),
    path(
        "<int:quote_id>/configurator/",
        views.configurator_view,
        name="configurator",
    ),
    path(
        "<int:quote_id>/items/add/",
        views.add_quote_item_view,
        name="add_quote_item",
    ),
    path(
        "<int:quote_id>/items/<int:item_id>/delete/",
        views.delete_quote_item_view,
        name="delete_quote_item",
    ),
    path(
        "<int:quote_id>/transition/",
        views.transition_quote_view,
        name="transition_quote",
    ),
    path("<int:quote_id>/bom/", views.bom_detail_view, name="bom_detail"),
]
