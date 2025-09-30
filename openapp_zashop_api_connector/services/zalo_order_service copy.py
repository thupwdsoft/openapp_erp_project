import json
import logging
from datetime import datetime
import json, requests
from odoo import fields # type: ignore
from odoo.tools import format_datetime as odoo_format # type: ignore
from odoo.fields import Datetime as OdooDatetime # type: ignore
from odoo.fields import Datetime as OdooDatetime # type: ignore
from odoo import _  # type: ignore
from odoo.http import request  # type: ignore

from .zalo_utils import get_company_by_mini_app_id, make_json_response,generate_mac_sha256_order
from .zalo_loyalty_service import add_points

_logger = logging.getLogger(__name__)


def create_order(self, **kw):
    data = request.httprequest.data
    json_data = json.loads(data)

    mini_app_id = json_data.get("mini_app_id")
    zalo_id = json_data.get("zalo_id")
    delivery_method = json_data.get("deliveryMethod", "pickup")
    payment_method_code = json_data.get("paymentMethod")
    app_trans_id = json_data.get("app_trans_id")
    order_note = json_data.get("orderNote", "")
    order_name = json_data.get("orderName", "")
    order_date_raw = json_data.get("orderDate", "")
    commitment_date_raw = json_data.get("receivedAt", "")
    shipping_address_id = json_data.get("shippingId")
    cart_items = json_data.get("cartItems", [])
    amount = json_data.get("amount", 0)
    source = json_data.get("source", "zalo-miniapp")
    mac_received = json_data.get("mac")

    # Validate cơ bản
    if not mini_app_id or not mini_app_id.isdigit():
        return make_json_response({"error": "Invalid Mini App ID"}, status=400)

    company = get_company_by_mini_app_id(mini_app_id)
    if not company:
        return make_json_response({"error": "Thiếu thông tin company."}, status=400)

    if not cart_items or amount <= 0:
        return make_json_response({"error": "Thiếu thông tin giỏ hàng hoặc tổng tiền không hợp lệ."}, status=400)

    partner = request.env["res.partner"].sudo().search([("zalo_id", "=", zalo_id)], limit=1)
    if not partner:
        return make_json_response({"error": "Không tìm thấy người dùng với zalo_id"}, status=404)

    partner_shipping_id = partner.id
    if delivery_method == "shipping":
        if not shipping_address_id:
            return make_json_response({"error": "Không có shippingId."}, status=400)
        shipping = request.env["res.partner"].sudo().browse(int(shipping_address_id))
        if not shipping.exists():
            return make_json_response({"error": "Địa chỉ giao hàng không tồn tại"}, status=400)
        partner_shipping_id = shipping.id

    payment_method = request.env["payment.method"].sudo().search([("code", "=", payment_method_code)], limit=1)
    if not payment_method:
        return make_json_response({"error": f"Không tìm thấy phương thức thanh toán: {payment_method_code}"}, status=400)

    # Parse ngày
    try:
        order_date = fields.Datetime.from_string(datetime.strptime(order_date_raw, "%Y-%m-%d %H:%M:%S"))
    except Exception:
        _logger.warning("⛔ Lỗi parse orderDate: %s → dùng ngày hiện tại", order_date_raw)
        order_date = fields.Datetime.now()

    try:
        commitment_date = fields.Datetime.to_string(datetime.strptime(commitment_date_raw, "%Y-%m-%d %H:%M:%S"))
    except Exception:
        _logger.warning("⛔ Lỗi parse receivedAt: %s → dùng order_date", commitment_date_raw)
        commitment_date = fields.Datetime.to_string(order_date)

    # ✅ Kiểm tra MAC nếu được truyền
    if mac_received:
        secret_key = company.zalo_secret_key or ""
        mac_expected = generate_mac_sha256_order(
            app_id=company.zalo_app_id,
            app_trans_id=app_trans_id,
            zalo_id=zalo_id,
            amount=amount,
            timestamp=json_data.get("timestamp"),
            secret_key=company.zalo_secret_key or ""
        )

        if mac_received != mac_expected:
            _logger.warning("❌ MAC không hợp lệ. Received: %s, Expected: %s", mac_received, mac_expected)
            return make_json_response({"error": "MAC không hợp lệ"}, status=403)

    # Tạo hoặc lấy utm source
    utm_source = request.env["utm.source"].sudo().search([("name", "=", source)], limit=1)
    if not utm_source:
        utm_source = request.env["utm.source"].sudo().create({"name": source})

    # ✅ Tạo đơn hàng
    sale_order = request.env["sale.order"].sudo().create({
        "partner_id": partner.id,
        "partner_invoice_id": partner.id,
        "partner_shipping_id": partner_shipping_id,
        "app_trans_id": app_trans_id,
        "state": "sale",
        "date_order": order_date,
        "commitment_date": commitment_date,
        "note": order_note,
        "delivery_method": delivery_method,
        "payment_method_id": payment_method.id,
        "company_id": company.id,
        "source_id": utm_source.id,
        "amount_total": amount,
    })

    for item in cart_items:
        product_id = item.get("item_id")
        product = request.env["product.product"].sudo().browse(int(product_id))
        if not product.exists():
            return make_json_response({"error": f"Sản phẩm {product_id} không tồn tại!"}, status=404)

        request.env["sale.order.line"].sudo().create({
            "order_id": sale_order.id,
            "product_id": product.id,
            "product_uom_qty": item["item_quantity"],
            "price_unit": item["item_price"],
            "name": item["item_name"],
        })

    # ✅ Cộng điểm
    add_points({
        "mini_app_id": mini_app_id,
        "zalo_id": zalo_id,
        "point_case": "order",
        "amount_total": amount
    })

    return make_json_response(format_order_response(sale_order))



def get_orders(kw):
    _logger.info("🔥 Gọi get_orders với payload: %s", kw)
    data = request.httprequest.data
    json_data = json.loads(data)

    mini_app_id = json_data.get("mini_app_id")
    partner_id = json_data.get("partner_id")
    states = json_data.get("states")  # Mảng các trạng thái Odoo như: ["sale", "done", "cancel"]

    if not mini_app_id or not partner_id:
        return {"success": False, "error": "Thiếu mini_app_id hoặc partner_id"}

    company = get_company_by_mini_app_id(mini_app_id)
    if not company:
        return {"success": False, "error": "Không tìm thấy công ty tương ứng với mini_app_id"}

    domain = [
        ("partner_id", "=", partner_id),
        ("company_id", "=", company.id),
    ]

    if states and isinstance(states, list):
        domain.append(("state", "in", states))

    orders = request.env["sale.order"].sudo().search(domain, order="date_order desc")

    def map_order_state(order):
        """Ánh xạ trạng thái đơn hàng từ Odoo sang frontend 'status' rõ ràng hơn"""
        if order.state == "cancel":
            return "cancel"
        if order.state == "sale" and all(picking.state == "done" for picking in order.picking_ids):
            return "shipping"
        if order.state == "done":
            return "completed"
        if order.state == "sale":
            return "pending"
        return "pending"
    for order in orders:
        _logger.info("📝 Order %s - commitment_date: %s | date_order: %s", order.name, order.commitment_date, order.date_order)

    return {
        "success": True,
        "orders": [
            {
                "order_id": order.id,
                "company_id": order.company_id.id,
                "name": order.name,
                "state": order.state,
                "status": map_order_state(order),  # Trạng thái dùng cho frontend
                "total_amount": order.amount_total,
                "date_order": order.date_order.strftime("%d/%m/%Y %H:%M"),
                "create_date": order.create_date.strftime("%d/%m/%Y %H:%M"),
                "received_at": (
                    order.commitment_date.strftime("%d/%m/%Y %H:%M")
                    if order.commitment_date
                    else order.date_order.strftime("%d/%m/%Y %H:%M")
                ),

                "delivery_method": order.delivery_method,
                "note": order.note or "",
                "payment_status": order.payment_status,
                "payment_method": order.payment_method_id.name if order.payment_method_id else "",
                "app_trans_id": order.app_trans_id,
                "shipping_info": {
                    "id": order.partner_shipping_id.id,
                    "partner_id": order.partner_shipping_id.parent_id.id if order.partner_shipping_id.parent_id else 0,
                    "alias": order.partner_shipping_id.name,
                    "address": order.partner_shipping_id.street or "",
                    "name": order.partner_shipping_id.name,
                    "phone": order.partner_shipping_id.phone or "",
                } if order.delivery_method == "shipping" and order.partner_shipping_id else None,
                "order_lines": [
                    {
                        "product_id": line.product_id.id,
                        "product_name": line.product_id.name,
                        "quantity": line.product_uom_qty,
                        "price_unit": line.price_unit,
                        "total_price": line.price_subtotal,
                        "image": line.product_id.image_1920 and f"/web/image/product.product/{line.product_id.id}/image_1920" or None,
                    }
                    for line in order.order_line
                ],
            }
            for order in orders
        ]
    }

def send_order_status_webhook(order):
    try:
        payload = {
            "order_id": order.id,
            "order_code": order.name,
            "state": order.state,
            "amount_total": order.amount_total,
            "partner_id": order.partner_id.id,
            "updated_at": order.write_date.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Thay bằng webhook n8n của bạn
        webhook_url = "https://searching.com.vn/api/webhook/order-status"

        response = requests.post(webhook_url, json=payload, timeout=5)
        _logger.info("Webhook response: %s", response.text)

    except Exception as e:
        _logger.exception("❌ Gửi webhook thất bại: %s", str(e))

def format_order_response(sale_order):
    return {
        "success": True,
        "order_id": sale_order.id,
        "order_name": sale_order.name
    }

def save_shipping_address(kwargs):
    shipping_id = kwargs.get("id")
    mini_app_id = kwargs.get("mini_app_id")
    partner_id = kwargs.get("partner_id")
    name = kwargs.get("name", "Người nhận")
    phone = kwargs.get("phone", "")
    address = kwargs.get("address", "")
    alias = kwargs.get("alias", "")

    if not partner_id or not address:
        return make_json_response({"error": "partner_id và address là bắt buộc"}, status=400)

    company = get_company_by_mini_app_id(mini_app_id)
    if not company:
        return make_json_response({"error": "Không tìm thấy công ty từ mini_app_id"}, status=400)

    company_id = company.id
    Partner = request.env['res.partner'].sudo()

    if shipping_id:
        shipping = Partner.browse(int(shipping_id))
        if not shipping.exists():
            return make_json_response({"error": f"Shipping address ID {shipping_id} không tồn tại."}, status=404)

        if shipping.company_id and shipping.company_id.id != company_id:
            return make_json_response({"error": "Địa chỉ này thuộc công ty khác."}, status=400)

        shipping.write({
            'name': name,
            'phone': phone,
            'street': address,
            'street2': alias,
        })
    else:
        shipping = Partner.create({
            'parent_id': int(partner_id),
            'company_id': company_id,
            'type': 'delivery',
            'name': name,
            'phone': phone,
            'street': address,
            'street2': alias,
        })

    return make_json_response({
        "error": 0,
        "message": "success",
        "data": {
            "id": shipping.id,
            "partner_id": shipping.parent_id.id,
            "name": shipping.name,
            "phone": shipping.phone,
            "address": shipping.street,
            "alias": shipping.street2,
        }
    })

def get_shipping_address(kwargs):
    partner_id = kwargs.get("partner_id")
    if not partner_id:
        return {"error": 1, "message": "partner_id is required", "data": []}

    shipping_list = request.env['res.partner'].sudo().search([
        ('parent_id', '=', int(partner_id)),
        ('type', '=', 'delivery')
    ], order="create_date desc")

    return {
        "error": 0,
        "message": "success",
        "data": [
            {
                "id": addr.id,
                "partner_id": addr.parent_id.id,
                "alias": addr.street2 or addr.name,
                "name": addr.name,
                "phone": addr.phone,
                "address": addr.street,
            } for addr in shipping_list
        ]
    }
