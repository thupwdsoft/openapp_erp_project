# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class OpenAppBoQ(models.Model):
    _name = "openapp.boq"
    _description = "Khối lượng dự toán (BoQ)"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        "Số BoQ",
        default=lambda s: s.env['ir.sequence'].next_by_code('openapp.boq'),
        required=True, tracking=True
    )
    project_id = fields.Many2one("project.project", string="Dự án", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Khách hàng", tracking=True)
    state = fields.Selection([("draft","Nháp"),("confirmed","Đã xác nhận")], default="draft", tracking=True)
    line_ids = fields.One2many("openapp.boq.line","boq_id", string="Dòng BoQ")

    amount_total = fields.Monetary("Tổng tiền", compute="_compute_amount", currency_field="currency_id", store=True)
    currency_id = fields.Many2one("res.currency", default=lambda s: s.env.company.currency_id.id)

    @api.depends("line_ids.total_price")
    def _compute_amount(self):
        for r in self:
            r.amount_total = sum(r.line_ids.mapped("total_price"))

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})


class OpenAppBoQLine(models.Model):
    _name = "openapp.boq.line"
    _description = "Dòng BoQ"
    _order = "sequence,id"

    boq_id = fields.Many2one("openapp.boq", required=True, ondelete="cascade")
    sequence = fields.Integer("STT", default=10)

    name = fields.Char("Diễn giải")
    product_id = fields.Many2one("product.product", string="Vật tư/Công việc")
    uom_id = fields.Many2one("uom.uom", string="ĐVT")
    quantity = fields.Float("Khối lượng", default=1.0)
    price_unit = fields.Monetary("Đơn giá", currency_field="currency_id")
    total_price = fields.Monetary("Thành tiền", compute="_compute_total", store=True, currency_field="currency_id")
    currency_id = fields.Many2one(related="boq_id.currency_id", store=True)

    @api.depends("quantity", "price_unit")
    def _compute_total(self):
        for l in self:
            q = l.quantity or 0.0
            p = l.price_unit or 0.0
            l.total_price = q * p

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for l in self:
            # Gợi ý ĐVT theo SP
            l.uom_id = l.product_id.uom_id.id if l.product_id else False
            # (Tuỳ chọn) gợi ý đơn giá theo list_price 
            if l.product_id:
                 l.price_unit = l.product_id.list_price

    @api.constrains("quantity", "price_unit")
    def _check_positive_numbers(self):
        for l in self:
            if l.quantity is not None and l.quantity < 0:
                raise ValidationError(_("Khối lượng phải >= 0."))
            if l.price_unit is not None and l.price_unit < 0:
                raise ValidationError(_("Đơn giá phải >= 0."))
