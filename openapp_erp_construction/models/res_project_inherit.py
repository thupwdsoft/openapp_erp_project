# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProjectProject(models.Model):
    _inherit = "project.project"

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Tài khoản phân tích",
        ondelete="set null",
        index=True,
        check_company=True,
    )

    design_document_ids = fields.Many2many(
        "ir.attachment",
        string="Tài liệu/Thiết kế",
        help="Đính kèm hồ sơ thiết kế, bản vẽ, spec, tiêu chuẩn… của dự án."
    )
    document_count = fields.Integer(compute="_compute_document_count", readonly=True)

    @api.depends('design_document_ids')
    def _compute_document_count(self):
        Att = self.env['ir.attachment'].sudo()
        for rec in self:
            rec.document_count = Att.search_count([
                ('res_model', '=', 'project.project'),
                ('res_id', '=', rec.id),
            ])

    # ---- helper: lấy/ tạo analytic plan mặc định cho công ty
    def _get_or_create_company_plan(self, company):
        Plan = self.env['account.analytic.plan'].with_company(company).sudo()
        # 1) ưu tiên plan đã gắn trên công ty (nếu có field này)
        plan = getattr(company, 'analytic_plan_id', False)
        if not plan:
            # 2) tìm plan bất kỳ của công ty
            plan = Plan.search([('company_id', '=', company.id)], limit=1)
        if not plan:
            # 3) không có thì tạo plan mặc định
            plan = Plan.create({
                'name': (company.name or 'Default') + ' Plan',
                'company_id': company.id,
            })
        return plan

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for p in projects:
            if not p.analytic_account_id:
                company = p.company_id or self.env.company
                plan = self._get_or_create_company_plan(company)
                aa_vals = {
                    "name": p.name or _("Project %s") % p.id,
                    "company_id": company.id,
                    "plan_id": plan.id,           # >>>>>>> quan trọng
                }
                aa = self.env["account.analytic.account"].with_company(company).sudo().create(aa_vals)
                p.analytic_account_id = aa.id
        return projects

    def write(self, vals):
        res = super().write(vals)
        if "name" in vals:
            for p in self.filtered('analytic_account_id'):
                try:
                    p.analytic_account_id.sudo().name = p.name
                except Exception:
                    pass
        return res
