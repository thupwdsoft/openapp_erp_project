# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProjectTask(models.Model):
    _inherit = "project.task"

    design_document_ids = fields.Many2many(
        "ir.attachment",
        string="Tài liệu/Thiết kế",
        help="Đính kèm hồ sơ, bản vẽ, spec… của task.",
    )

    def action_open_design_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Tài liệu/Thiết kế"),
            "res_model": "ir.attachment",
            "view_mode": "kanban,tree,form",
            "domain": [("res_model", "=", "project.task"), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": "project.task",
                "default_res_id": self.id,
            },
            "target": "current",
        }
