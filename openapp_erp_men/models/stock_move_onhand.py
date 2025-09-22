# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_qty_onhand_src = fields.Float(
        string="SL tồn (nguồn)",
        compute='_compute_x_qty_onhand_src',
        digits='Product Unit of Measure'
    )

    @api.depends('product_id', 'location_id')
    def _compute_x_qty_onhand_src(self):
        Quant = self.env['stock.quant'].sudo()
        for m in self:
            qty = 0.0
            if m.product_id and m.location_id:
                # tồn sẵn sàng = quantity - reserved_quantity (gộp location con)
                quants = Quant.read_group(
                    domain=[('product_id', '=', m.product_id.id),
                            ('location_id', 'child_of', m.location_id.id)],
                    fields=['quantity:sum', 'reserved_quantity:sum'],
                    groupby=[]
                )
                if quants:
                    q = quants[0]
                    qty = (q.get('quantity_sum') or 0.0) - (q.get('reserved_quantity_sum') or 0.0)
            m.x_qty_onhand_src = qty
