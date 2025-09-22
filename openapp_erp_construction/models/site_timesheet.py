# -*- coding: utf-8 -*-
from odoo import models, fields, api, _  # type: ignore

TS_STATE = [('draft', 'Nháp'), ('confirmed', 'Đã xác nhận')]


class OpenAppSiteTimesheet(models.Model):
    _name = 'openapp.site.timesheet'
    _description = 'Chấm công công trường'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        default=lambda s: s.env['ir.sequence'].next_by_code('openapp.site.ts'),
        readonly=True,
    )
    employee_id = fields.Many2one('hr.employee', string="Nhân viên", required=True)
    user_id = fields.Many2one(related='employee_id.user_id', store=True, readonly=True)
    project_id = fields.Many2one('project.project', string="Dự án", required=True)
    task_id = fields.Many2one('project.task', string="Hạng mục")
    date = fields.Date(default=fields.Date.context_today, required=True, string="Ngày")
    hours = fields.Float("Số giờ", default=8.0)
    cost_rate = fields.Float("Đơn giá công", help="VNĐ/giờ hoặc theo currency công ty")
    amount = fields.Monetary("Thành tiền", compute="_compute_amount", store=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id.id)
    state = fields.Selection(TS_STATE, default='draft', tracking=True)
    analytic_line_id = fields.Many2one('account.analytic.line', string="Bút toán phân tích", readonly=True)

    @api.depends('hours', 'cost_rate')
    def _compute_amount(self):
        for r in self:
            r.amount = (r.hours or 0.0) * (r.cost_rate or 0.0)

    def action_confirm(self):
        """
        Tạo account.analytic.line ghi nhận chi phí nhân công.
        Nếu cần tạo Analytic Account cho dự án: tự dò & gán plan_id theo biến thể (company_id/company_ids),
        chỉ khi field plan_id tồn tại và là bắt buộc.
        """
        AAL = self.env['account.analytic.line']
        fields_in_line = AAL._fields

        for r in self:
            if r.state != 'draft':
                continue

            # Base values
            vals = {
                'name': _("Nhân công %s") % (r.employee_id.name or ''),
                'date': r.date,
                'unit_amount': r.hours or 0.0,
                'amount': -(r.amount or 0.0),  # Chi phí -> số âm
            }

            # Optional fields (chỉ gán khi field tồn tại)
            if 'employee_id' in fields_in_line and r.employee_id:
                vals['employee_id'] = r.employee_id.id
            if 'project_id' in fields_in_line and r.project_id:
                vals['project_id'] = r.project_id.id
            if 'task_id' in fields_in_line and r.task_id:
                vals['task_id'] = r.task_id.id

            # Chuẩn bị account_id (analytic)
            if 'account_id' in fields_in_line:
                analytic = False

                # Ưu tiên analytic đã gán trên dự án (nếu model có field)
                if (
                    r.project_id
                    and 'analytic_account_id' in r.project_id._fields
                    and r.project_id.analytic_account_id
                ):
                    analytic = r.project_id.analytic_account_id

                # Fallback: tạo analytic cho dự án nếu chưa có
                if not analytic and r.project_id:
                    company = r.project_id.company_id or self.env.company
                    AnalyticAccount = self.env['account.analytic.account'].with_company(company)

                    create_vals = {
                        'name': r.project_id.display_name or r.project_id.name,
                        # account.analytic.account bản chuẩn có company_id
                        'company_id': getattr(r.project_id, 'company_id', company).id,
                    }

                    # Nếu có field plan_id & là bắt buộc thì tìm/ tạo plan phù hợp
                    if 'plan_id' in AnalyticAccount._fields and AnalyticAccount._fields['plan_id'].required:
                        Plan = self.env['account.analytic.plan'].with_company(company).sudo()
                        plan_domain = []
                        # Một số bản có company_id (m2o), số khác dùng company_ids (m2m), hoặc không ràng buộc
                        if 'company_id' in Plan._fields:
                            plan_domain = [('company_id', '=', company.id)]
                        elif 'company_ids' in Plan._fields:
                            plan_domain = [('company_ids', 'in', company.id)]

                        plan = Plan.search(plan_domain, limit=1) or Plan.search([], limit=1)
                        if not plan:
                            plan_create_vals = {'name': _('Default')}
                            if 'company_id' in Plan._fields:
                                plan_create_vals['company_id'] = company.id
                            elif 'company_ids' in Plan._fields:
                                plan_create_vals['company_ids'] = [(6, 0, [company.id])]
                            plan = Plan.create(plan_create_vals)

                        create_vals['plan_id'] = plan.id

                    analytic = AnalyticAccount.sudo().create(create_vals)

                    # Liên kết ngược analytic về Project nếu có field
                    if 'analytic_account_id' in r.project_id._fields:
                        r.project_id.analytic_account_id = analytic.id

                if analytic:
                    vals['account_id'] = analytic.id

            aal = AAL.create(vals)
            r.write({'analytic_line_id': aal.id, 'state': 'confirmed'})

    def action_open_analytic(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'form',
            'res_id': self.analytic_line_id.id,
        }
