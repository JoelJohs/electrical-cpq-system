"""Señales para invalidación inteligente de caché en catálogo y compatibilidades."""

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from catalog.models import Product, ProductCompatibility

CACHE_VERSION_KEY = "catalog:cache_version"


def get_cache_version() -> int:
    """Retorna la versión activa de la caché del catálogo."""
    return cache.get_or_set(CACHE_VERSION_KEY, 1)


def bump_cache_version() -> int:
    """Incrementa la versión de la caché invalidando atómicamente todas las entradas."""
    try:
        new_version = cache.incr(CACHE_VERSION_KEY)
    except (ValueError, Exception):
        current = cache.get(CACHE_VERSION_KEY, 1)
        new_version = current + 1
        cache.set(CACHE_VERSION_KEY, new_version)
    return new_version


@receiver([post_save, post_delete], sender=Product)
def invalidate_on_product_change(sender, instance, **kwargs):
    """Invalida la caché del catálogo ante cambios de productos."""
    bump_cache_version()


@receiver([post_save, post_delete], sender=ProductCompatibility)
def invalidate_on_compatibility_change(sender, instance, **kwargs):
    """Invalida la caché del grafo de compatibilidad ante cualquier modificación."""
    bump_cache_version()
