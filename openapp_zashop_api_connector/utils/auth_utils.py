# -*- coding: utf-8 -*-
import logging
from odoo import http

_logger = logging.getLogger(__name__)


def get_api_key(params):
    """
    Ưu tiên lấy api_key từ query params, nếu không có thì lấy từ header
    """
    return params.get("api_key") or http.request.httprequest.headers.get("x-api-key")


def verify_app_key(env, params):
    """
    Xác thực app_id và api_key theo bản ghi trong model zalo.mini.app
    """
    app_id = params.get("app_id")
    api_key = get_api_key(params)

    if not app_id or not api_key:
        _logger.warning("[Zalo API] Thiếu app_id hoặc api_key")
        return False

    app = get_zalo_mini_app(env, app_id)
    if not app:
        _logger.warning(f"[Zalo API] Không tìm thấy Mini App với app_id `{app_id}`")
        return False

    if app.secret_key != api_key:
        _logger.warning(f"[Zalo API] app_id `{app_id}` có api_key không hợp lệ.")
        return False

    return True


def get_zalo_mini_app(env, app_id):
    """
    Trả về bản ghi zalo.mini.app theo app_id
    """
    return env['zalo.mini.app'].sudo().search([
        ('name', '=', app_id),
        ('active', '=', True)
    ], limit=1)


def unauthorized_response():
    """
    Trả về lỗi 401 nếu xác thực thất bại
    """
    return {
        "success": False,
        "error": "unauthorized",
        "message": "Invalid app_id or api_key"
    }, 401
