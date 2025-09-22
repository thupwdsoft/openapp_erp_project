# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ # type: ignore
from ._open_record_mixin import OpenRecordActionMixin

class OpenAppSubcontract(models.Model):
    _name = "openapp.subcontract"
    _description = "Hợp đồng thầu phụ"
    _order = "id desc"
    _inherit = ["mail.thread","mail.activity.mixin","openapp.open_record_action_mixin"]

    name = fields.Char("Số HĐ", default=lambda s:s.env['ir.sequence'].next_by_code('openapp.subcontract'), required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Nhà thầu phụ", required=True)
    project_id = fields.Many2one("project.project", string="Dự án", required=True)
    amount_total = fields.Monetary("Giá trị HĐ", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda s:s.env.company.currency_id.id)
    state = fields.Selection([("draft","Nháp"),("running","Đang thực hiện"),("done","Hoàn tất")], default="draft", tracking=True)

    purchase_order_ids = fields.Many2many("purchase.order", string="PO thầu phụ")
    purchase_count = fields.Integer(compute="_compute_counts", string="Số đơn mua")

    @api.depends("purchase_order_ids")
    def _compute_counts(self):
        for r in self:
            r.purchase_count = len(r.purchase_order_ids)

    def action_view_purchase_orders(self):
        self.ensure_one()
        return self._action_open_records(
            "purchase.order",
            self.purchase_order_ids,
            _("Đơn mua hàng thầu phụ"),
            "purchase.purchase_order_form"
        )
