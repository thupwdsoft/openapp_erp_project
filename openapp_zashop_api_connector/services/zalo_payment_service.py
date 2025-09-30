from dataclasses import fields
import hashlib
import hmac
import json
import logging

from requests import request

from .zalo_utils import get_company_by_mini_app_id


_logger = logging.getLogger(__name__)

def zalo_payment_callback(kw):
    try:
        raw_data = request.httprequest.data
        json_data = json.loads(raw_data.decode("utf-8"))

        # mini_app_id lấy từ body, query hoặc header
        mini_app_id = (
            json_data.get("app_id")
            or request.params.get("mini_app_id")
            or request.httprequest.headers.get("X-Zalo-MiniApp-ID")
        )

        if not mini_app_id:
            _logger.warning("Không tìm thấy mini_app_id từ callback")
            return {"code": -1, "message": "Missing mini_app_id"}

        # Tìm công ty
        company = get_company_by_mini_app_id(mini_app_id)

        if not company or not company.zalo_app_secret:
            _logger.warning("Không tìm thấy công ty hoặc thiếu secret key")
            return {"code": -1, "message": "Missing company config"}

        # Xác thực chữ ký MAC từ Zalo
        received_mac = json_data.get("mac")
        app_id = json_data.get("app_id")
        app_trans_id = json_data.get("app_trans_id")
        zp_trans_id = json_data.get("zp_trans_id")
        user_id = json_data.get("user", {}).get("id")
        amount = json_data.get("amount")
        server_time = json_data.get("server_time")

        data_string = f"{app_id}|{app_trans_id}|{zp_trans_id}|{user_id}|{amount}|{server_time}"
        mac_calculated = hmac.new(
            company.zalo_app_secret.encode("utf-8"),
            data_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if mac_calculated != received_mac:
            _logger.warning("Zalo Signature mismatch")
            return {"code": -1, "message": "Invalid signature"}

        # Parse embed_data để lấy app_trans_id gốc bạn tạo từ frontend
        try:
            embed_data = json.loads(json_data.get("embed_data", "{}"))
        except Exception:
            embed_data = {}
        original_trans_id = embed_data.get("app_trans_id")

        if not original_trans_id:
            _logger.warning("Không tìm thấy app_trans_id trong embed_data")
            return {"code": -1, "message": "Missing app_trans_id"}

        # Tìm đơn hàng theo app_trans_id (gốc bạn sinh ra từ frontend)
        sale_order = request.env["sale.order"].sudo().search([
            ("app_trans_id", "=", original_trans_id)
        ], limit=1)

        if not sale_order:
            _logger.warning(f"Không tìm thấy đơn hàng theo app_trans_id: {original_trans_id}")
            return {"code": -1, "message": "Order not found"}

        # Cập nhật trạng thái thanh toán cho đơn hàng
        sale_order.write({
            "payment_status": "paid",
            "zalo_transaction_id": zp_trans_id,
            "zalo_payment_at": fields.Datetime.fromtimestamp(json_data.get("payment_time")),
        })

        _logger.info("Đã cập nhật thanh toán thành công cho đơn hàng %s", original_trans_id)
        return {"code": 0, "message": "Callback processed successfully"}

    except Exception as e:
        _logger.error("Callback error: %s", str(e))
        return {"code": -2, "message": "Server error"}
