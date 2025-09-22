# -*- coding: utf-8 -*-
from odoo import models, fields

class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Liên kết MR để theo dõi truy vết
    openapp_mr_id = fields.Many2one(
        "openapp.material.request", string="MR", index=True
    )
    project_id = fields.Many2one(
        "project.project",
        related="openapp_mr_id.project_id",
        store=True, readonly=True,
    )

    def _action_done(self):
        """
        Sau khi kho xác nhận DONE, đồng bộ lại tiến độ MR:
        - Cập nhật qty_delivered theo move_line.quantity (đã quy đổi UoM)
        - Cập nhật tổng tiến độ + trạng thái MR (auto 'done' nếu giao đủ)
        """
        res = super()._action_done()
        mrs = self.filtered('openapp_mr_id').mapped('openapp_mr_id')
        if mrs:
            mrs._recompute_lines_delivered()
            mrs._compute_delivery_progress()
            mrs._sync_state_from_pickings()
        return res
