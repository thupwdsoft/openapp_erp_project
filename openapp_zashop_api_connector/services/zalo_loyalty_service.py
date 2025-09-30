import logging
from odoo.http import request  # type: ignore
from odoo import fields  # type: ignore

from .zalo_utils import get_company_by_mini_app_id, make_json_response

_logger = logging.getLogger(__name__)


def add_points(kwargs):
    try:
        mini_app_id = kwargs.get("mini_app_id")
        zalo_id = kwargs.get('zalo_id')
        point_case = kwargs.get('point_case', 'manual')
        reason = ''
        points = 0

        company = get_company_by_mini_app_id(mini_app_id)
        if not company:
            return make_json_response({"error": "Thiếu thông tin company."}, status=400)

        partner = request.env['res.partner'].sudo().search([('zalo_id', '=', zalo_id)], limit=1)
        if not partner:
            return {"error": "Không tìm thấy người dùng với zalo_id"}

        program = request.env['loyalty.program'].sudo().search([
            ('company_id', '=', company.id),
            ('program_type', '=', 'gift_card'),
            ('trigger', '=', 'auto'),
            ('applies_on', '=', 'future'),
            ('date_from', '<=', fields.Date.today()),
            '|', ('date_to', '>=', fields.Date.today()), ('date_to', '=', False)
        ], limit=1)

        card = request.env['loyalty.card'].sudo().search([
            ('partner_id', '=', partner.id),
            ('company_id', '=', company.id),
            ('program_id', '=', program.id)
        ], limit=1)

        if not card:
            card = request.env['loyalty.card'].sudo().create({
                'partner_id': partner.id,
                'company_id': company.id,
                'program_id': program.id if program else None,
                'points': 0,
                'active': True,
            })

        # Xử lý logic theo case
        if point_case == "order":
            amount = float(kwargs.get("amount_total", 0))
            points = int(amount // 10000)
            reason = f"Tích điểm theo đơn hàng ({amount}đ)"
        elif point_case == "signup":
            points = 10
            reason = "Tặng điểm khi đăng ký thành viên mới"
        elif point_case == "referral":
            referrer_zalo_id = kwargs.get("referrer_zalo_id")
            if not referrer_zalo_id:
                return {"error": "Thiếu referrer_zalo_id"}
            referrer = request.env['res.partner'].sudo().search([('zalo_id', '=', referrer_zalo_id)], limit=1)
            if referrer:
                ref_card = request.env['loyalty.card'].sudo().search([
                    ('partner_id', '=', referrer.id),
                    ('company_id', '=', company.id)
                ], limit=1)
                if not ref_card:
                    ref_card = request.env['loyalty.card'].sudo().create({
                        'partner_id': referrer.id,
                        'company_id': company.id,
                        'program_id': program.id if program else None,
                    })
                ref_card.points += 10
                ref_card.sudo().write({'points': ref_card.points})
                request.env['loyalty.history'].sudo().create({
                    'card_id': ref_card.id,
                    'action': 'add',
                    'points': 10,
                    'description': f"Nhận điểm giới thiệu từ {zalo_id}"
                })
            points = 10
            reason = "Được bạn giới thiệu - tặng điểm"
        elif point_case == "event":
            event_name = kwargs.get("event_name", "sự kiện đặc biệt")
            points = int(kwargs.get("points", 5))
            reason = f"Tặng điểm từ sự kiện: {event_name}"
        else:
            points = int(kwargs.get("points", 0))
            reason = kwargs.get("reason", "Cộng điểm thủ công")

        card.points += points
        card.sudo().write({'points': card.points})

        request.env['loyalty.history'].sudo().create({
            'card_id': card.id,
            'action': 'add',
            'points': points,
            'description': reason,
        })

        return {"success": True, "new_point": card.points, "message": reason}

    except Exception as e:
        _logger.exception("Lỗi khi cộng điểm: %s", str(e))
        return {"error": "Lỗi hệ thống", "detail": str(e)}


def get_points(kwargs):
    try:
        mini_app_id = kwargs.get("mini_app_id")
        zalo_id = kwargs.get("zalo_id")

        company = get_company_by_mini_app_id(mini_app_id)
        if not company:
            return make_json_response({"error": "Thiếu thông tin company."}, status=400)

        partner = request.env["res.partner"].sudo().search([("zalo_id", "=", zalo_id)], limit=1)
        if not partner:
            return {"error": "Không tìm thấy người dùng"}

        program = request.env['loyalty.program'].sudo().search([
            ('company_id', '=', company.id),
            ('program_type', '=', 'gift_card'),
            ('trigger', '=', 'auto'),
            ('applies_on', '=', 'future'),
            '|', ('date_to', '>=', fields.Date.today()), ('date_to', '=', False)
        ], limit=1)

        card = request.env["loyalty.card"].sudo().search([
            ("partner_id", "=", partner.id),
            ("company_id", "=", company.id),
            ("program_id", "=", program.id if program else False)
        ], limit=1)

        if not card:
            return {"points": 0, "card_id": None}

        return {
            "success": True,
            "points": card.points,
            "card_id": card.id,
            "program_id": card.program_id.id if card.program_id else None,
            "expiration_date": card.expiration_date
        }

    except Exception as e:
        _logger.exception("Lỗi khi lấy điểm: %s", str(e))
        return {"error": "Lỗi hệ thống", "detail": str(e)}


def redeem_points(kwargs):
    try:
        mini_app_id = kwargs.get("mini_app_id")
        zalo_id = kwargs.get("zalo_id")
        points_to_redeem = int(kwargs.get("points", 0))
        reward_name = kwargs.get("reward_name", "Đổi thưởng")

        company = get_company_by_mini_app_id(mini_app_id)
        if not company:
            return make_json_response({"error": "Thiếu thông tin company."}, status=400)

        if points_to_redeem <= 0:
            return {"error": "Số điểm đổi không hợp lệ"}

        partner = request.env["res.partner"].sudo().search([("zalo_id", "=", zalo_id)], limit=1)
        if not partner:
            return {"error": "Không tìm thấy người dùng"}

        program = request.env['loyalty.program'].sudo().search([
            ('company_id', '=', company.id),
            ('program_type', '=', 'gift_card'),
            ('trigger', '=', 'auto'),
            ('applies_on', '=', 'future'),
            '|', ('date_to', '>=', fields.Date.today()), ('date_to', '=', False)
        ], limit=1)

        card = request.env["loyalty.card"].sudo().search([
            ("partner_id", "=", partner.id),
            ("company_id", "=", company.id),
            ("program_id", "=", program.id if program else False)
        ], limit=1)

        if not card or card.points < points_to_redeem:
            return {"error": "Không đủ điểm để đổi thưởng"}

        card.points -= points_to_redeem
        card.sudo().write({'points': card.points})

        request.env["loyalty.history"].sudo().create({
            "card_id": card.id,
            "action": "redeem",
            "points": -points_to_redeem,
            "description": f"Đổi thưởng: {reward_name}"
        })

        return {
            "success": True,
            "message": f"Đã đổi {points_to_redeem} điểm lấy {reward_name}",
            "remaining_points": card.points
        }

    except Exception as e:
        _logger.exception("Lỗi khi đổi điểm: %s", str(e))
        return {"error": "Lỗi hệ thống", "detail": str(e)}
