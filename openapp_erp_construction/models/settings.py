# -*- coding: utf-8 -*-
from odoo import models, fields # type: ignore

class ResCompany(models.Model):
    _inherit = "res.company"
    openapp_retention_account_id = fields.Many2one("account.account", string="Retention Account")
    openapp_retention_journal_id = fields.Many2one("account.journal", string="Retention Journal")

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    openapp_retention_account_id = fields.Many2one(related="company_id.openapp_retention_account_id", readonly=False)
    openapp_retention_journal_id = fields.Many2one(related="company_id.openapp_retention_journal_id", readonly=False)
