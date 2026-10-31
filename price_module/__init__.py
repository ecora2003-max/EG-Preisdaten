"""Offline-first, side-effect-free reference delivery for EG-Architecture 1.0.0-draft."""
from .service import PriceService, provider_registry, parse_quantity, cents, resolve_stores
__all__ = ["PriceService", "provider_registry", "parse_quantity", "cents", "resolve_stores"]
