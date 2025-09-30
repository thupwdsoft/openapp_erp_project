# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request

class ZaloHelpdeskAPI(http.Controller):
    @http.route("/zalo/helpdesk/api/v1/tickets", type="json", auth="user", methods=["POST"], csrf=False)
    def create_ticket(self, **payload):
        vals = payload or {}
        if not vals.get("description"):
            return {"ok": False, "error": _("Thiếu mô tả (description).")}
        team_id = request.env.ref("openapp_warranty.helpdesk_team_warranty_repair").id
        ticket = request.env["helpdesk.ticket"].sudo().create({
            "name": vals.get("subject") or _("Yêu cầu từ Zalo"),
            "description": vals.get("description"),
            "partner_id": vals.get("partner_id"),
            "team_id": team_id,
            "ticket_type": vals.get("ticket_type") or "warranty",
        })
        return {"ok": True, "ticket_id": ticket.id, "name": ticket.display_name}
