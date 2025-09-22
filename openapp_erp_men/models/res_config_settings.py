from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    enforce_stock_on_sale = fields.Boolean(
        string="Chặn xác nhận Đơn bán khi thiếu tồn",
        config_parameter="openapp_core.enforce_stock_on_sale",
        default=True,
    )
    enforce_stock_on_delivery = fields.Boolean(
        string="Chặn xác nhận Giao hàng khi chưa được reserve",
        config_parameter="openapp_core.enforce_stock_on_delivery",
        default=True,
    )
