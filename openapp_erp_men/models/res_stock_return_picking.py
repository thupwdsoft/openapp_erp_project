# models/stock_return_picking.py
# -*- coding: utf-8 -*-
from odoo import api, models

class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    @api.onchange('picking_id')
    def _oa_onchange_picking_id_set_qty(self):
        """
        Gọi sau super() đã dựng các dòng → set quantity = 1 cho dòng đang = 0.
        Tương thích nhiều tên O2M khác nhau giữa các phiên bản/addon.
        """
        res = super()._onchange_picking_id() if hasattr(super(), "_onchange_picking_id") else None
        for o2m in ("product_return_moves", "move_ids", "line_ids"):
            lines = getattr(self, o2m, False)
            if lines:
                for ln in lines:
                    if not ln.quantity:
                        ln.quantity = 1.0
        return res



class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    @api.model
    def create(self, vals):
        """
        Ép mặc định quantity = 1 nếu chưa có hoặc = 0.
        Làm ở tầng create để chắc chắn ngay khi hệ thống dựng dòng wizard.
        """
        if not vals.get("quantity"):
            vals["quantity"] = 1.0
        return super().create(vals)