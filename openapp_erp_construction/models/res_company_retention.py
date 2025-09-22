# -*- coding: utf-8 -*-
from odoo import models, fields # type: ignore

class ResCompany(models.Model):
    _inherit = 'res.company'

    openapp_project_consume_location_id = fields.Many2one(
        'stock.location', string="Địa điểm tiêu hao công trình"
    )
    
    openapp_retention_receivable_id = fields.Many2one(
        'account.account', string="TK phải thu giữ lại",
        domain="[('company_id', '=', id), ('internal_type', '=', 'receivable'), ('deprecated', '=', False)]"
    )
    openapp_retention_payable_id = fields.Many2one(
        'account.account', string="TK phải trả giữ lại",
        domain="[('company_id', '=', id), ('internal_type', '=', 'payable'), ('deprecated', '=', False)]"
    )
    openapp_retention_reclass_enabled = fields.Boolean(
        string="Tự động hạch toán Retention khi vào sổ", default=True
    )
