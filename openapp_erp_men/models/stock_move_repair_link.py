# -*- coding: utf-8 -*-
from odoo import fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    # Inverse cho repair.order.move_ids
    repair_id = fields.Many2one(
        'repair.order',
        string='Repair Order',
        index=True,
        ondelete='set null',
    )
