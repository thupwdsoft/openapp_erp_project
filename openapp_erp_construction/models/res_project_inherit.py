# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProjectProject(models.Model):
    _inherit = "project.project"

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Tài khoản phân tích",
        ondelete="set null",
        index=True,
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

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for p in projects:
            if not p.analytic_account_id:
                aa = self.env["account.analytic.account"].create({
                    "name": p.name or _("Project %s") % p.id,
                    "company_id": p.company_id.id,
                })
                p.analytic_account_id = aa.id
        return projects

    def write(self, vals):
        res = super().write(vals)
        if "name" in vals:
            for p in self.filtered('analytic_account_id'):
                try:
                    p.analytic_account_id.name = p.name
                except Exception:
                    pass
        return res
