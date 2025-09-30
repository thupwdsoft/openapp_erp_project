# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    # ===== Liên kết bảo hành / ticket (giữ tối thiểu, không đụng core stock/sale) =====
    under_warranty = fields.Boolean(string="Đang được bảo hành")
    is_warranty = fields.Boolean(string="Bảo hành")

    warranty_card_id = fields.Many2one(
        "warranty.card", string="Phiếu bảo hành",
        ondelete="set null", index=True, copy=False
    )
    ticket_id = fields.Many2one(
        "helpdesk.ticket", string="Ticket bảo hành",
        ondelete="set null", index=True, copy=False
    )

    # Dùng trong view để khóa trường nguồn khi đã gắn Ticket/Card
    source_locked = fields.Boolean(compute="_compute_source_locked", store=False)

    @api.depends("ticket_id", "warranty_card_id")
    def _compute_source_locked(self):
        for r in self:
            r.source_locked = bool(r.ticket_id or r.warranty_card_id)

    # ===== ONCHANGE: đồng bộ từ Ticket =====
    @api.onchange("ticket_id")
    def _onchange_ticket_id(self):
        for r in self:
            t = r.ticket_id
            if not t:
                continue

            # Gợi ý phiếu BH từ ticket (nếu có)
            if not r.warranty_card_id and getattr(t, "warranty_card_id", False):
                r.warranty_card_id = t.warranty_card_id.id

            # Khách hàng
            if not r.partner_id and getattr(t, "partner_id", False):
                r.partner_id = t.partner_id.id

            # Sản phẩm + UoM
            prod = getattr(t, "warranty_product_id", False) or getattr(t, "product_id", False)
            if prod and not r.product_id:
                r.product_id = prod.id
                r.product_uom = prod.uom_id.id

            # Lot/Serial
            lot = getattr(t, "warranty_lot_id", False) or getattr(t, "lot_id", False)
            if lot and not r.lot_id:
                r.lot_id = lot.id

            # Cờ bảo hành
            is_warr = bool(
                getattr(t, "is_warranty", False)
                or (getattr(t, "warranty_card_id", False) and t.warranty_card_id.state == "active")
            )
            r.under_warranty = is_warr
            r.is_warranty = is_warr

    # ===== ONCHANGE: đồng bộ từ Phiếu bảo hành =====
    @api.onchange("warranty_card_id")
    def _onchange_warranty_card_id(self):
        for r in self:
            c = r.warranty_card_id
            if not c:
                continue

            if not r.partner_id and getattr(c, "partner_id", False):
                r.partner_id = c.partner_id.id

            if getattr(c, "product_id", False) and not r.product_id:
                r.product_id = c.product_id.id
                r.product_uom = c.product_id.uom_id.id

            if getattr(c, "lot_id", False) and not r.lot_id:
                r.lot_id = c.lot_id.id

            # Có card thì mặc định là bảo hành
            r.under_warranty = True
            r.is_warranty = True

    # ===== (Tuỳ chọn) Khi bật bảo hành, mặc định miễn phí linh kiện ADD nếu có field =====
    @api.onchange("under_warranty")
    def _onchange_under_warranty_default_billable(self):
        if not self.under_warranty:
            return
        for m in self.move_ids:
            # chỉ xử lý khi có đủ field, tránh lỗi nếu module billable bị gỡ
            if getattr(m, "repair_line_type", None) == "add" and "repair_billable" in m._fields and m.repair_billable:
                m.repair_billable = False

    # ===== CREATE/WRITE: đồng bộ 2 cờ bảo hành =====
    @api.model_create_multi
    def create(self, vals_list):
        cleaned = []
        for vals in vals_list:
            if isinstance(vals, dict):
                cleaned.append({k: v for k, v in vals.items() if k in self._fields})
        return super().create(cleaned)

    def write(self, vals):
        if "under_warranty" in vals and "is_warranty" not in vals:
            vals["is_warranty"] = bool(vals["under_warranty"])
        if "is_warranty" in vals and "under_warranty" not in vals:
            vals["under_warranty"] = bool(vals["is_warranty"])
        return super().write(vals)
