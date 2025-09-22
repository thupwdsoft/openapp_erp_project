# -*- coding: utf-8 -*-
from odoo import models, fields # type: ignore

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    openapp_retention_receivable_id = fields.Many2one(
        related='company_id.openapp_retention_receivable_id', readonly=False
    )
    openapp_retention_payable_id = fields.Many2one(
        related='company_id.openapp_retention_payable_id', readonly=False
    )
    openapp_retention_reclass_enabled = fields.Boolean(
        related='company_id.openapp_retention_reclass_enabled', readonly=False
    )

    openapp_project_consume_location_id = fields.Many2one(
        related='company_id.openapp_project_consume_location_id', readonly=False
    )