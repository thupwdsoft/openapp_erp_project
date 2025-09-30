# -*- coding: utf-8 -*-
from odoo import fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Ảnh của biến thể (nếu không có, Odoo tự fallback từ template)
    product_image_128 = fields.Image(
        string="Ảnh SP",
        related="product_id.image_128",
        readonly=True,
    )
