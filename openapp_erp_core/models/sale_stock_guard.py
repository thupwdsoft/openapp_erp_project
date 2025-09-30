# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        # Cho phép bật/tắt bằng config param (mặc định BẬT)
        param = self.env["ir.config_parameter"].sudo()
        enforce = param.get_param("openapp_core.enforce_stock_on_sale", "1") != "0"

        if enforce:
            for order in self:
                wh = order.warehouse_id  # có sẵn khi cài sale_stock
                if not wh:
                    # Không có kho trên đơn => bỏ qua kiểm tồn (hoặc raise tuỳ bạn)
                    continue

                # Chỉ kiểm cho hàng lưu kho
                lines = order.order_line.filtered(lambda l: l.product_id.type == "product" and l.product_uom_qty > 0)
                shortages = []
                for l in lines:
                    # đổi về UoM gốc của product để so với virtual_available
                    qty_need = l.product_uom._compute_quantity(l.product_uom_qty, l.product_id.uom_id)
                    avail = (l.product_id
                               .with_company(order.company_id)
                               .with_context(warehouse=wh.id)
                               .virtual_available) or 0.0
                    if avail < qty_need:
                        shortages.append((l.product_id.display_name, avail, qty_need, wh.name))

                if shortages:
                    msg_lines = [
                        _("- %(p)s: Dự báo %(a).2f < Cần %(n).2f (Kho: %(w)s)") % {
                            "p": p, "a": a, "n": n, "w": w
                        } for (p, a, n, w) in shortages
                    ]
                    raise UserError(
                        _("Không đủ tồn kho để xác nhận đơn bán:\n") + "\n".join(msg_lines)
                    )

        return super().action_confirm()
