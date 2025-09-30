import requests
import json
import logging
from odoo import _  # type: ignore
from odoo.http import request  # type: ignore

from .zalo_utils import generate_hmac_sha256, get_company_by_mini_app_id, make_json_response, get_zalo_app_from_config
from ..utils.config import ZALO_GET_PHONE_URL, ZALO_GRAPH_URL_V2

_logger = logging.getLogger(__name__)


def get_or_create_user(kw):
    try:
        data = request.httprequest.data
        json_data = json.loads(data)

        _logger.info("Body nhận được từ Mini App: %s", json_data)

        app_id = json_data.get("app_id")
        mini_app_id = json_data.get("mini_app_id")
        access_token = json_data.get("access_token")
        phone_token = json_data.get("phone_token")

        if not access_token:
            return make_json_response({"error": "Thiếu Access Token"}, status=400)
        if not phone_token:
            return make_json_response({"error": "Thiếu Phone Token"}, status=400)
        if not mini_app_id:
            return make_json_response({"error": "Thiếu Mini App ID"}, status=400)

        company = get_company_by_mini_app_id(mini_app_id)
        if not company:
            return make_json_response({"error": "Không tìm thấy công ty với mini_app_id"}, status=404)

        app = get_zalo_app_from_config(request.env, app_id)
        if not app:
            return make_json_response({"error": "Không tìm thấy cấu hình Mini App"}, status=404)

        user_info = get_zalo_user_info(access_token, phone_token, app.secret_key, company.id)
        if not user_info or "id" not in user_info:
            _logger.error(f"Không lấy được thông tin từ Zalo với access_token: {access_token}")
            return make_json_response({"error": "Không lấy được thông tin từ Zalo hoặc Access Token không hợp lệ"}, status=400)

        zalo_id = user_info.get("id")

        user = request.env["res.partner"].sudo().search([("zalo_id", "=", zalo_id)], limit=1)

        if user:
            if user.company_id.id != company.id:
                user = request.env["res.partner"].sudo().create({
                    "parent_id": company.partner_id.id,
                    "company_id": company.id,
                    "name": user_info.get("name", "Unknown User"),
                    "phone": user_info.get("phone", ""),
                    "zalo_id": zalo_id,
                    "zalo_avatar": user_info.get("picture", {}).get("data", {}).get("url", ""),
                    "refresh_token": user_info.get("refresh_token"),
                })
            else:
                updates = {}

                if not user.phone and user_info.get("phone"):
                    updates["phone"] = user_info["phone"]

                if not user.parent_id or user.parent_id.id != company.partner_id.id:
                    updates["parent_id"] = company.partner_id.id

                if updates:
                    user.sudo().write(updates)

            return make_json_response(format_user_response(user, company.id))


        new_user = request.env["res.partner"].sudo().create({
            "parent_id": company.partner_id.id,
            "company_id": company.id,
            "name": user_info.get("name", "Unknown User"),
            "phone": user_info.get("phone", ""),
            "zalo_id": zalo_id,
            "zalo_avatar": user_info.get("picture", {}).get("data", {}).get("url", ""),
            "refresh_token": user_info.get("refresh_token"),
        })

        return make_json_response(format_user_response(new_user, company.id))

    except Exception as e:
        _logger.error(f"Lỗi khi lấy hoặc tạo user: {str(e)}")
        return make_json_response({"error": "Lỗi khi lấy hoặc tạo user.", "details": str(e)}, status=500)


def get_zalo_user_info(zalo_access_token, user_phone_token, zalo_app_secret_key, company_id):
    appsecret_proof = generate_hmac_sha256(zalo_access_token, zalo_app_secret_key)

    try:
        response = requests.get(
            ZALO_GRAPH_URL_V2,
            headers={
                "access_token": zalo_access_token,
                "appsecret_proof": appsecret_proof,
            },
            params={
                "fields": "id,name,birthday,picture"
            }
        )

        if response.status_code == 200:
            user_info = response.json()
            phone_info = get_phone_number_from_token(zalo_access_token, user_phone_token, zalo_app_secret_key)
            if phone_info and "data" in phone_info and "number" in phone_info["data"]:
                user_info["phone"] = phone_info["data"]["number"]
            return user_info

        elif response.status_code == 100:
            handle_expired_token(company_id)
        else:
            _logger.error("Zalo user info error: %s", response.text)

    except Exception as e:
        _logger.exception("Exception when fetching Zalo user info: %s", str(e))

    return {"error": "Không thể lấy thông tin người dùng Zalo."}

def get_phone_number_from_token(zalo_access_token, token, secret_key):
    try:
        response = requests.get(
            ZALO_GET_PHONE_URL,
            params={
                "access_token": zalo_access_token,
                "code": token,
                "secret_key": secret_key,
            }
        )

        _logger.info("Response status code: %s", response.status_code)
        _logger.info("Response content: %s", response.text)

        if response.status_code == 200:
            return response.json()
        else:
            _logger.error("Lỗi lấy số điện thoại từ Zalo: %s", response.text)
            return None

    except Exception as e:
        _logger.exception("Exception khi lấy số điện thoại Zalo: %s", str(e))
        return None


def handle_expired_token(company_id):
    user = request.env["res.partner"].sudo().search(
        [("company_id", "=", company_id), ("refresh_token", "!=", False)], limit=1
    )

    if not user:
        _logger.error("Không tìm thấy refresh_token cho user nào.")
        return None

    new_access_token, new_refresh_token = refresh_access_token(user)

    if new_access_token:
        user.sudo().write({"refresh_token": new_refresh_token})
        _logger.info("Refresh Token được cập nhật thành công!")
        return get_zalo_user_info(new_access_token, company_id)

    _logger.error("Làm mới Access Token thất bại.")
    return None

def refresh_access_token(user):
    from ..utils.config import ZALO_REFRESH_TOKEN_URL
    from .zalo_utils import get_zalo_mini_app_by_id

    app = get_zalo_mini_app_by_id(request.env, user.company_id.mini_app_id)
    if not app:
        _logger.error("Không tìm thấy cấu hình Mini App khi làm mới token")
        return None, None

    data = {
        "app_id": app.name,
        "grant_type": "refresh_token",
        "refresh_token": user.refresh_token,
        "app_secret": app.secret_key,
    }

    try:
        response = requests.post(ZALO_REFRESH_TOKEN_URL, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
        _logger.info("API Refresh Token Response: %s", response.text)

        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token"), token_data.get("refresh_token")

        _logger.error("Lỗi khi làm mới Access Token: %s", response.text)
        return None, None
    except requests.RequestException as e:
        _logger.error("RequestException khi làm mới Access Token: %s", str(e))
        return None, None


def format_user_response(user, company_id):
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "zalo_id": user.zalo_id,
        "zalo_avatar": user.zalo_avatar,
        "company_id": company_id,
    }