# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ._open_record_mixin import OpenRecordActionMixin  # giữ y như mã của anh

STATE = [
    ("draft", "Nháp"),
    ("submitted", "Đã gửi"),
    ("approved", "Phê duyệt"),
    ("done", "Hoàn tất"),
]

class OpenAppMaterialRequest(models.Model):
    _name = "openapp.material.request"
    _description = "Yêu cầu vật tư (MR)"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin", "openapp.open_record_action_mixin"]

    # ==== THÔNG TIN CHUNG (HEADER) ====
    name = fields.Char(
        string="Số MR",
        default=lambda s: s.env["ir.sequence"].next_by_code("openapp.mr"),
        required=True, tracking=True, readonly=True,
    )
    project_id = fields.Many2one(
        "project.project", string="Dự án", required=True, tracking=True,
        help="Công trình/Dự án yêu cầu cấp vật tư."
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Tài khoản phân tích",
        compute="_compute_analytic_account", store=True, readonly=True,
        help="Tự lấy từ Dự án để phục vụ hạch toán chi phí."
    )
    date = fields.Date(
        string="Ngày yêu cầu",
        default=fields.Date.context_today
    )
    state = fields.Selection(
        STATE, string="Tình trạng", default="draft", tracking=True
    )

    # ==== DÒNG VẬT TƯ (LINES) ====
    line_ids = fields.One2many(
        "openapp.material.request.line", "mr_id",
        string="Dòng vật tư"
    )

    # ==== LIÊN KẾT KHO (STOCK LINKS) ====
    picking_ids = fields.One2many(
        "stock.picking", "openapp_mr_id",
        string="Phiếu kho", readonly=True
    )
    picking_count = fields.Integer(
        string="Số phiếu kho",
        compute="_compute_counts"
    )

    # ==== TIẾN ĐỘ GIAO (PROGRESS) ====
    qty_requested = fields.Float(
        string="SL yêu cầu",
        compute="_compute_delivery_progress"
    )
    qty_delivered = fields.Float(
        string="SL đã giao",
        compute="_compute_delivery_progress"
    )
    delivery_progress = fields.Float(
        string="Tiến độ giao (%)",
        compute="_compute_delivery_progress",
        help="Tỷ lệ = (SL đã giao / SL yêu cầu) × 100%"
    )
    delivery_done = fields.Boolean(
        string="Đã giao đủ",
        compute="_compute_delivery_progress",
        help="Đánh dấu khi tổng SL đã giao ≥ SL yêu cầu."
    )


    # ================== COMPUTE / HELPERS ==================
    @api.depends(
        "line_ids.quantity",
        "picking_ids.state",
        "picking_ids.move_line_ids.quantity",         # schema của anh: quantity (không phải qty_done)
        "picking_ids.move_line_ids.product_uom_id",
    )
    def _compute_delivery_progress(self):
        """
        delivered = tổng move_line.quantity (ở các picking DONE) sau khi quy đổi
        về UoM của product tương ứng.
        """
        for mr in self:
            requested = sum(mr.line_ids.mapped("quantity")) or 0.0
            mr.qty_requested = requested

            if not requested or not mr.picking_ids:
                mr.qty_delivered = 0.0
                mr.delivery_progress = 0.0
                mr.delivery_done = False
                continue

            delivered = 0.0
            done_pickings = mr.picking_ids.filtered(lambda p: p.state == "done")
            if done_pickings:
                for ml in done_pickings.mapped("move_line_ids"):
                    if not ml.product_id:
                        continue
                    # Quy đổi từ UoM trên move line về UoM của product
                    qty = ml.product_uom_id._compute_quantity(
                        ml.quantity, ml.product_id.uom_id, round=False
                    )
                    delivered += qty

            mr.qty_delivered = delivered
            mr.delivery_progress = 0.0 if not requested else min(100.0, (delivered / requested) * 100.0)
            mr.delivery_done = delivered >= (requested - 1e-6)

    def _recompute_lines_delivered(self):
        """
        Cập nhật SL đã giao trên từng dòng MR (gom theo product).
        Lưu ý: gom tất cả phiếu kho DONE của MR, quy đổi UoM chính xác.
        """
        for mr in self:
            if not mr.line_ids:
                continue
            done_pickings = mr.picking_ids.filtered(lambda p: p.state == "done")
            if not done_pickings:
                mr.line_ids.update({"qty_delivered": 0.0})
                continue

            delivered_map = {}
            for ml in done_pickings.mapped("move_line_ids"):
                if not ml.product_id:
                    continue
                qty = ml.product_uom_id._compute_quantity(
                    ml.quantity, ml.product_id.uom_id, round=False
                )
                delivered_map[ml.product_id.id] = delivered_map.get(ml.product_id.id, 0.0) + qty

            for ln in mr.line_ids:
                ln.qty_delivered = delivered_map.get(ln.product_id.id, 0.0)

    def _sync_state_from_pickings(self):
        for mr in self:
            mr._compute_delivery_progress()  # đảm bảo số mới nhất
            if mr.delivery_done and mr.state in ("submitted", "approved"):
                mr.state = "done"

    # ================== ACTIONS / BUTTONS ==================
    def action_view_pickings(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').sudo().read()[0]
        action['name'] = _("Phiếu kho")
        action['domain'] = [('openapp_mr_id', '=', self.id)]
        action['views'] = [(False, 'list'), (False, 'form')]
        return action

    @api.depends("project_id")
    def _compute_analytic_account(self):
        for r in self:
            r.analytic_account_id = (
                r.project_id.analytic_account_id.id
                if r.project_id and "analytic_account_id" in r.project_id._fields
                else False
            )

    @api.depends("picking_ids")
    def _compute_counts(self):
        for r in self:
            r.picking_count = len(r.picking_ids)

    # ---- Lifecycle ----
    def action_submit(self):
        self.write({"state": "submitted"})

    def action_approve(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_("MR chưa có dòng vật tư."))
        self.write({"state": "approved"})

    def action_done(self):
        """
        Cho phép bấm Hoàn tất ngay trên MR để ép đồng bộ tiến độ
        (trường hợp kho đã DONE trước).
        """
        self._recompute_lines_delivered()
        self._compute_delivery_progress()
        self._sync_state_from_pickings()
        return True

    # ================== STOCK CREATION (Optional) ==================
    def action_create_internal_transfer(self):
        """
        Tạo phiếu xuất kho theo từng dòng MR.
        - Lấy picking type 'outgoing'
        - Mặc định src = Stock, dest = Customers (hoặc cấu hình công ty)
        - Ghi 'openapp_mr_id' để truy vết
        """
        self.ensure_one()
        if self.state == "draft":
            self.action_submit()
        if self.state == "submitted":
            self.action_approve()

        if not self.line_ids:
            raise UserError(_("MR chưa có dòng vật tư."))

        PickingType = self.env["stock.picking.type"].sudo()
        picking_type = PickingType.search([('code', '=', 'outgoing')], limit=1) \
                       or self.env.ref('stock.picking_type_out')

        src_loc = picking_type.default_location_src_id or self.env.ref('stock.stock_location_stock')
        dest_loc = (self.env.company.openapp_project_consume_location_id
                    if hasattr(self.env.company, "openapp_project_consume_location_id") and self.env.company.openapp_project_consume_location_id
                    else self.env.ref('stock.stock_location_customers'))

        Picking = self.env["stock.picking"].sudo()
        Move = self.env["stock.move"].sudo()

        picking = Picking.create({
            "picking_type_id": picking_type.id,
            "location_id": src_loc.id,
            "location_dest_id": dest_loc.id,
            "origin": self.name,
            "openapp_mr_id": self.id,
            # (tuỳ chọn) hiển thị địa chỉ giao hàng
            "partner_id": getattr(self.project_id, "partner_id", False) and self.project_id.partner_id.id or False,
        })

        for l in self.line_ids:
            vals = {
                "name": l.product_id.display_name,
                "product_id": l.product_id.id,
                "product_uom_qty": l.quantity,      # số lượng yêu cầu
                "product_uom": l.uom_id.id,         # UoM của DÒNG MR (độc lập)
                "location_id": src_loc.id,
                "location_dest_id": dest_loc.id,
                "picking_id": picking.id,
            }
            if self.analytic_account_id and 'analytic_distribution' in Move._fields:
                vals["analytic_distribution"] = {str(self.analytic_account_id.id): 100}
            Move.create(vals)

        return self._action_open_records("stock.picking", picking, _("Phiếu xuất (MR)"))


class OpenAppMaterialRequestLine(models.Model):
    _name = "openapp.material.request.line"
    _description = "Dòng yêu cầu vật tư"
    _order = "id"

    mr_id = fields.Many2one(
        "openapp.material.request",
        string="Phiếu MR",
        required=True,
        ondelete="cascade",
        help="Phiếu Yêu cầu vật tư (MR) cha."
    )
    product_id = fields.Many2one(
        "product.product",
        string="Vật tư",
        required=True,
        help="Mã vật tư/sản phẩm cần cấp."
    )

    # ĐVT của DÒNG MR (độc lập, không related về product)
    uom_id = fields.Many2one(
        "uom.uom",
        string="Đơn vị tính",
        required=True,
        help="Đơn vị tính của dòng MR (mặc định theo vật tư)."
    )

    quantity = fields.Float(
        string="Số lượng yêu cầu",
        default=1.0,
        help="Số lượng xin cấp theo đơn vị tính của dòng."
    )

    description = fields.Char(
        string="Ghi chú",
        help="Mô tả/ghi chú thêm cho dòng vật tư (nếu có)."
    )

    # Cập nhật tự động từ kho
    qty_delivered = fields.Float(
        string="Số lượng đã giao",
        readonly=True,
        help="Tổng số lượng đã xuất thực tế (quy đổi về ĐVT của vật tư)."
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for r in self:
            r.uom_id = r.product_id.uom_id.id if r.product_id else False

    def write(self, vals):
        if any(l.mr_id.state == 'done' for l in self):
            raise UserError(_("Phiếu MR đã Hoàn tất, không được sửa dòng."))
        return super().write(vals)

    def unlink(self):
        if any(l.mr_id.state == 'done' for l in self):
            raise UserError(_("Phiếu MR đã Hoàn tất, không được xóa dòng."))
        return super().unlink()