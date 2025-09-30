# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        # Cho phép bật/tắt bằng config param (mặc định BẬT)
        enforce = self.env["ir.config_parameter"].sudo().get_param(
            "openapp_core.enforce_stock_on_delivery", "1"
        ) != "0"

        if enforce:
            for picking in self:
                # Chỉ áp dụng cho phiếu Xuất hàng (outgoing)
                if getattr(picking, "picking_type_code", "") != "outgoing":
                    continue
                # Yêu cầu các move của hàng lưu kho phải ở trạng thái 'assigned' (đã được dự trữ đủ)
                not_assigned = picking.move_ids_without_package.filtered(
                    lambda m: m.product_id.type == "product" and m.state != "assigned"
                )
                if not_assigned:
                    names = ", ".join(not_assigned.mapped("product_id.display_name"))
                    raise UserError(
                        _("Chưa đủ tồn kho để giao hàng. Hãy bấm 'Check Availability' và chỉ validate khi trạng thái là 'Ready'.\nSản phẩm: %s") % names
                    )

        return super().button_validate()
