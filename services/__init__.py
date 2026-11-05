"""
Services package for Relate (LuxStore).
"""
from services.auth_service import (
    load_db,
    save_db,
    register_user,
    authenticate_user,
    update_user_name,
    change_user_password,
    reset_password_with_hash,
)
from services.email_service import (
    request_password_reset_otp,
    verify_password_reset_otp,
    is_otp_verified,
    consume_verified_otp,
)
from services.recommendation_service import (
    RecommenderSystem,
    get_product_dict_list,
    get_product_dict_list_with_reasons,
)

__all__ = [
    "load_db",
    "save_db",
    "register_user",
    "authenticate_user",
    "update_user_name",
    "change_user_password",
    "reset_password_with_hash",
    "request_password_reset_otp",
    "verify_password_reset_otp",
    "is_otp_verified",
    "consume_verified_otp",
    "RecommenderSystem",
    "get_product_dict_list",
    "get_product_dict_list_with_reasons",
]

