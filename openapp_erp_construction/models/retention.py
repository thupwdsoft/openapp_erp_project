# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

RET_STATES = [('open', 'Đang giữ'), ('released', 'Đã nhả'), ('cancel', 'Hủy')]

# ==============================
# Kế thừa account.move (invoice)
# ==============================
class AccountMove(models.Model):
    _inherit = 'account.move'

    retention_percent = fields.Float(string="Tỷ lệ giữ lại (%)", digits=(16, 2), tracking=True)
    retention_amount = fields.Monetary(string="Số tiền giữ lại",
                                       compute="_compute_retention_amount", store=True)
    retention_release_date = fields.Date(string="Ngày dự kiến nhả", tracking=True)
    has_retention = fields.Boolean(string="Có giữ lại?",
                                   compute="_compute_has_retention", store=True)
    
    # --- COUNT + ACTION mở ledger từ hóa đơn ---
    retention_ledger_count = fields.Integer(
        string="Số dòng giữ lại", compute="_compute_retention_ledger_count"
    )

    def _compute_retention_ledger_count(self):
        Ledger = self.env['openapp.retention.ledger']
        for inv in self:
            inv.retention_ledger_count = Ledger.search_count([('move_id', '=', inv.id)])

    def action_open_retention_ledger(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Giữ lại của chứng từ"),
            "res_model": "openapp.retention.ledger",
            "view_mode": "list,form,pivot,graph",   # <-- thay tree bằng list
            "domain": [("move_id", "=", self.id)],
            "context": {"search_default_group_by_partner": 1, "default_move_id": self.id},
            "target": "current",
        }

    @api.depends('amount_untaxed', 'retention_percent', 'currency_id')
    def _compute_retention_amount(self):
        for m in self:
            base = m.amount_untaxed or 0.0
            val = base * (m.retention_percent or 0.0) / 100.0
            m.retention_amount = m.currency_id.round(val) if m.currency_id else round(val, 2)

    @api.depends('retention_amount', 'retention_percent')
    def _compute_has_retention(self):
        for m in self:
            m.has_retention = bool((m.retention_percent or 0.0) > 0 and (m.retention_amount or 0.0) > 0)

    # ---------- Helper: lấy Project an toàn ----------
    def _get_project_for_retention(self, inv):
        project_id = False
        SaleOrder = self.env['sale.order']
        # 1) Qua SO nếu có field project_id (có module sale_project / sale_timesheet)
        if 'project_id' in SaleOrder._fields:
            so_projects = inv.invoice_line_ids.mapped('sale_line_ids.order_id.project_id')
            so_projects = so_projects.filtered(lambda p: p)
            if so_projects:
                project_id = so_projects[0].id
            elif inv.invoice_origin:
                so = SaleOrder.search([('name', '=', inv.invoice_origin)], limit=1)
                if so and so.project_id:
                    project_id = so.project_id.id
        # 2) Fallback: qua analytic_distribution (JSON {aa_id: ratio})
        if not project_id:
            acc_ids = []
            for line in inv.invoice_line_ids:
                dist = line.analytic_distribution
                if isinstance(dist, dict):
                    for k in dist.keys():
                        try:
                            acc_ids.append(int(k))
                        except Exception:
                            continue
            if acc_ids:
                analytic = self.env['account.analytic.account'].browse(acc_ids).filtered('project_id')
                if analytic:
                    project_id = analytic[0].project_id.id
        return project_id

    # ------------- Reclass + Ledger khi post -------------
    def _post(self, soft=True):
        res = super()._post(soft=soft)

        for inv in self.filtered(lambda x: x.state == 'posted'
                                           and x.has_retention
                                           and x.move_type in ('out_invoice', 'in_invoice')):
            # 1) Ghi ledger
            project_id = self._get_project_for_retention(inv)
            self.env['openapp.retention.ledger'].sudo().create({
                'move_id': inv.id,
                'move_type': inv.move_type,
                'partner_id': inv.partner_id.id,
                'project_id': project_id or False,
                'company_id': inv.company_id.id,
                'currency_id': inv.currency_id.id,
                'amount_base': inv.amount_untaxed,
                'percent': inv.retention_percent,
                'amount': inv.retention_amount,
                'release_date': inv.retention_release_date,
            })

            # 2) Reclass (nếu bật cấu hình)
            if not inv.company_id.openapp_retention_reclass_enabled:
                continue

            amount = inv.retention_amount
            if not amount:
                continue

            if inv.move_type == 'out_invoice':
                ret_account = inv.company_id.openapp_retention_receivable_id
                ar_type = 'receivable'
                sign = 1  # DR Retention / CR AR
            else:  # in_invoice
                ret_account = inv.company_id.openapp_retention_payable_id
                ar_type = 'payable'
                sign = -1  # CR Retention / DR AP

            if not ret_account:
                inv.message_post(body=_("Chưa cấu hình tài khoản Retention tương ứng. Bỏ qua bút toán reclass."))
                continue

            ar_lines = inv.line_ids.filtered(
                lambda l: l.account_id.internal_type == ar_type and not l.reconciled
            )
            if not ar_lines:
                continue

            move_vals = {
                'date': inv.date or fields.Date.context_today(self),
                'ref': _("Retention reclass for %s") % inv.name,
                'journal_id': inv.journal_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': _("Retention for %s") % inv.name,
                        'partner_id': inv.partner_id.id,
                        'account_id': ret_account.id,
                        'debit': amount * (1 if sign == 1 else 0),
                        'credit': amount * (1 if sign == -1 else 0),
                    }),
                    (0, 0, {
                        'name': _("Retention reclass %s") % inv.name,
                        'partner_id': inv.partner_id.id,
                        'account_id': ar_lines[0].account_id.id,
                        'debit': amount * (1 if sign == -1 else 0),
                        'credit': amount * (1 if sign == 1 else 0),
                    }),
                ]
            }
            reclass = self.env['account.move'].create(move_vals)
            reclass.action_post()

            # 3) Reconcile tự động phần công nợ
            to_reconcile = ar_lines | reclass.line_ids.filtered(
                lambda l: l.account_id.internal_type == ar_type and l.partner_id == inv.partner_id
            )
            try:
                to_reconcile.reconcile()
            except Exception:
                # Không chặn quy trình nếu reconcile không thành công
                pass

        return res


# ==============================
# Sổ theo dõi Retention
# ==============================
class OpenAppRetentionLedger(models.Model):
    _name = 'openapp.retention.ledger'
    _description = "Sổ theo dõi giữ lại (Retention)"
    _order = "release_date asc, id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default=lambda s: s.env['ir.sequence'].next_by_code('openapp.retention'),
                       readonly=True)
    move_id = fields.Many2one('account.move', string="Chứng từ gốc", required=True, tracking=True)
    move_type = fields.Selection(related='move_id.move_type', store=True)
    partner_id = fields.Many2one('res.partner', string="Đối tác", required=True, tracking=True)
    project_id = fields.Many2one('project.project', string="Dự án")
    company_id = fields.Many2one('res.company', string="Công ty", required=True,
                                 default=lambda s: s.env.company.id)
    currency_id = fields.Many2one('res.currency', required=True,
                                  default=lambda s: s.env.company.currency_id.id)
    amount_base = fields.Monetary(string="Giá trị gốc")
    percent = fields.Float(string="Tỷ lệ (%)", digits=(16, 2))
    amount = fields.Monetary(string="Số tiền giữ lại")
    release_date = fields.Date(string="Ngày dự kiến trả nốt", tracking=True)
    state = fields.Selection(RET_STATES, default='open', tracking=True)
    released_move_id = fields.Many2one('account.move', string="Chứng từ công nợ giữ lại", readonly=True)

    def action_release_retention(self):
        for r in self:
            if r.state != 'open':
                raise UserError(_("Bản ghi đã xử lý."))
            if not r.amount:
                r.state = 'released'
                continue

            vals = {
                'move_type': 'out_invoice' if r.move_type == 'out_invoice' else 'in_invoice',
                'invoice_date': fields.Date.context_today(self),
                'partner_id': r.partner_id.id,
                'currency_id': r.currency_id.id,
                'invoice_origin': r.move_id.name,
                'invoice_line_ids': [(0, 0, {
                    'name': _("Thanh toán nốt phần công nợ giữ lại cho %s") % (r.move_id.name,),
                    'quantity': 1,
                    'price_unit': r.amount,
                })],
            }
            mv = self.env['account.move'].create(vals)
            mv.action_post()
            r.write({'state': 'released', 'released_move_id': mv.id})

    def action_open_move(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
        }

    def _cron_retention_reminder(self):
        """Cron: tạo activity nhắc nhở khi đến hạn nhả."""
        today = fields.Date.today()
        records = self.search([('state', '=', 'open'),
                               ('release_date', '!=', False),
                               ('release_date', '<=', today)])
        model_id = self.env['ir.model']._get_id('openapp.retention.ledger')
        todo_type = self.env.ref('mail.mail_activity_data_todo')
        for r in records:
            self.env['mail.activity'].create({
                'res_model_id': model_id,
                'res_id': r.id,
                'activity_type_id': todo_type.id,
                'user_id': self.env.user.id,
                'summary': _("Retention đến hạn nhả"),
                'note': _("Thanh toán nốt phần công nợ giữ lại cho %s, số tiền %s") % (r.move_id.display_name, r.amount),
            })
