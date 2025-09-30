# -*- coding: utf-8 -*-
from odoo import models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_open_quick_sale(self):
        """Mở form Báo giá, prefill 1 dòng với biến thể đầu tiên của sản phẩm."""
        self.ensure_one()
        product = self.product_variant_id  # luôn có ít nhất 1 biến thể

        ctx = {
            # Tạo sẵn 1 dòng sản phẩm
            "default_order_line": [(0, 0, {
                "product_id": product.id,
                "product_uom_qty": 1,
            })],
        }
        return {
            "name": "Báo giá",
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "target": "current",
            "context": ctx,
        }
