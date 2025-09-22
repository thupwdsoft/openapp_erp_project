from odoo import models, fields, api # type: ignore
from ._open_record_mixin import OpenRecordActionMixin
class OpenAppWorkCertificate(models.Model):
    _name="openapp.work.certificate"; _description="Chứng nhận khối lượng (Work Certificate)"; _order="id desc"
    _inherit=["mail.thread","mail.activity.mixin","openapp.open_record_action_mixin"]

    
    name=fields.Char("Số WC", default=lambda s:s.env['ir.sequence'].next_by_code('openapp.wc'), required=True, tracking=True)
    project_id=fields.Many2one("project.project", string="Dự án", required=True)
    date=fields.Date("Ngày", default=fields.Date.context_today)
    amount_certified=fields.Monetary("Giá trị nghiệm thu", currency_field="currency_id")
    retention_percent=fields.Float("Tỷ lệ giữ lại (%)", default=5.0)
    retention_amount=fields.Monetary("Tiền giữ lại", compute="_compute_retention", store=True, currency_field="currency_id")
    currency_id=fields.Many2one("res.currency", default=lambda s:s.env.company.currency_id.id)
    state=fields.Selection([("draft","Nháp"),("approved","Phê duyệt"),("invoiced","Đã lập hóa đơn")], default="draft", tracking=True)
    invoice_ids=fields.Many2many("account.move", string="Hóa đơn liên quan")

    @api.depends("amount_certified","retention_percent")
    def _compute_retention(self):
        for r in self: r.retention_amount=(r.amount_certified or 0.0)*(r.retention_percent or 0.0)/100.0
    
    def action_view_invoices(self):
        self.ensure_one(); return self._action_open_records("account.move", self.invoice_ids, "Hóa đơn khách hàng", "account.view_move_form")
