from odoo import models, fields, api, _
from odoo.exceptions import UserError  # nếu muốn chặn dữ liệu chưa hợp lệ
from ._open_record_mixin import OpenRecordActionMixin

class OpenAppVariationOrder(models.Model):
    _name = "openapp.variation.order"
    _description = "Lệnh thay đổi (VO)"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin", "openapp.open_record_action_mixin"]

    name = fields.Char("Số VO", default=lambda s: s.env['ir.sequence'].next_by_code('openapp.vo'),
                       required=True, tracking=True)
    project_id = fields.Many2one("project.project", string="Dự án", required=True)
    date = fields.Date("Ngày", default=fields.Date.context_today)
    description = fields.Text("Mô tả")
    amount_change = fields.Monetary("Giá trị thay đổi", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda s: s.env.company.currency_id.id)
    state = fields.Selection([("draft", "Nháp"), ("approved", "Phê duyệt")],
                             default="draft", tracking=True)
    so_ids = fields.Many2many("sale.order", string="Đơn bán liên quan")
    invoice_ids = fields.Many2many("account.move", string="Hóa đơn liên quan")

    # === actions ===
    def action_view_sale_orders(self):
        self.ensure_one()
        return self._action_open_records("sale.order", self.so_ids, "Đơn bán", "sale.view_order_form")

    def action_view_invoices(self):
        self.ensure_one()
        return self._action_open_records("account.move", self.invoice_ids, "Hóa đơn", "account.view_move_form")

    def action_approve(self):
        """Phê duyệt VO"""
        for r in self:
            if r.state != "draft":
                continue
            # (tuỳ chọn) kiểm tra dữ liệu trước khi duyệt
            # if not r.amount_change:
            #     raise UserError(_("Vui lòng nhập 'Giá trị thay đổi' trước khi phê duyệt."))
            r.state = "approved"

    def action_set_to_draft(self):
        """Đặt về nháp"""
        for r in self:
            if r.state != "approved":
                continue
            r.state = "draft"
