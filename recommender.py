"""
Backward-compatibility alias for services.recommendation_service.
"""
from services.recommendation_service import (
    RecommenderSystem,
    get_product_dict_list,
    get_product_dict_list_with_reasons,
)

__all__ = [
    "RecommenderSystem",
    "get_product_dict_list",
    "get_product_dict_list_with_reasons",
]
