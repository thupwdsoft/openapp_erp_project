import hashlib
import hmac
import logging
from bs4 import BeautifulSoup
import json
from odoo.http import request # type: ignore
from odoo.exceptions import ValidationError # type: ignore
from odoo import _ # type: ignore

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)  # Đảm bảo rằng mức log là INFO hoặc thấp hơn


def make_json_response(data, status=200):
    """Chuẩn hóa JSON response"""
    response_data = {
        "error": 0 if status == 200 else 1,
        "message": "Successful" if status == 200 else "Failed",
        "data": data
    }
    return request.make_response(
        json.dumps(response_data, ensure_ascii=False),
        headers=[('Content-Type', 'application/json')],
        status=status
    )

def validate_access_token(params):
    """Lấy access_token từ query hoặc headers"""
    access_token = (
        params.get("access_token")
        or request.httprequest.args.get("access_token")
        or request.httprequest.headers.get("X-Access-Token")
    )

    _logger.debug("🔹 Received access_token from params: %s", params.get("access_token"))
    _logger.debug("🔹 Received access_token from args: %s", request.httprequest.args.get("access_token"))
    _logger.debug("🔹 Received access_token from headers: %s", request.httprequest.headers.get("X-Access-Token"))

    if not access_token:
        raise ValidationError(_("Missing access_token"))

    return access_token

def validate_refresh_token(params):
    """Lấy refresh_token từ query hoặc headers"""
    refresh_token = (
        params.get("refresh_token")
        or request.httprequest.args.get("refresh_token")
        or request.httprequest.headers.get("X-Refresh-Token")
    )

    _logger.debug("🔹 Received refresh_token from params: %s", params.get("refresh_token"))
    _logger.debug("🔹 Received refresh_token from args: %s", request.httprequest.args.get("refresh_token"))
    _logger.debug("🔹 Received refresh_token from headers: %s", request.httprequest.headers.get("X-Refresh-Token"))

    if not refresh_token:
        raise ValidationError("Missing refresh_token")

    return refresh_token

def validate_mini_app_id(params):
    """Lấy mini_app_id từ query hoặc headers"""
    mini_app_id = (
        (params or {}).get("mini_app_id")
        or request.params.get("mini_app_id")
        or request.httprequest.args.get("mini_app_id")
        or request.httprequest.headers.get("X-Mini-App-Id")
    )

    _logger.debug("🔹 Received mini_app_id from params: %s", params.get("mini_app_id"))
    _logger.debug("🔹 Received mini_app_id from args: %s", request.httprequest.args.get("mini_app_id"))
    _logger.debug("🔹 Received mini_app_id from headers: %s", request.httprequest.headers.get("X-Mini-App-Id"))

    if not mini_app_id or not mini_app_id.isdigit():
        raise ValidationError("Invalid Mini App ID")

    return mini_app_id

def generate_hmac_sha256(data, secret_key):
        return hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

def generate_mac_sha256_order(app_id, app_trans_id, zalo_id, amount, timestamp, secret_key):
    data = f"{app_id}|{app_trans_id}|{zalo_id}|{amount}|{timestamp}"
    mac = hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()
    return mac

def get_company_by_mini_app_id(mini_app_id):
    """Truy vấn công ty cha (parent_id = False) theo mini_app_id"""
    company = request.env["res.company"].sudo().search([
        ("mini_app_id", "=", mini_app_id),
        ("parent_id", "=", False),
    ], limit=1)

    if not company:
        raise ValidationError("Parent company not found for the given Mini App ID")

    return company
   
def get_media_from_description(description_html):
    """Trích xuất URL hình ảnh và video từ mô tả thương mại điện tử"""
    if not description_html:
        return {"images": [], "videos": []}

    soup = BeautifulSoup(description_html, "html.parser")

    images = [img.get("src", "") for img in soup.find_all("img") if img.get("src")]
    videos = [video.get("src", "") for video in soup.find_all("video") if video.get("src")]
    iframes = [iframe.get("src", "") for iframe in soup.find_all("iframe") if iframe.get("src")]

    return {"images": images, "videos": videos + iframes}

def get_zalo_app_from_config(env, app_id):
    """
    Trả về bản ghi zalo.mini.app theo app_id (name).
    """
    _logger = logging.getLogger(__name__)

    app = env['zalo.mini.app'].sudo().search([
        ('name', '=', app_id),
        ('active', '=', True)
    ], limit=1)

    if not app:
        _logger.warning(f"[ZaloMiniApp] Không tìm thấy Mini App với app_id {app_id}")
        return None

    return app

