# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class OpenAppBoQ(models.Model):
    _name = "openapp.boq"
    _description = "Khối lượng dự toán (BoQ)"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        "Số BoQ",
        default=lambda s: s.env["ir.sequence"].next_by_code("openapp.boq"),
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Công ty",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )

    project_id = fields.Many2one("project.project", string="Dự án", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Khách hàng", tracking=True)

    pricelist_id = fields.Many2one("product.pricelist", string="Bảng giá")
    sale_order_id = fields.Many2one("sale.order", string="Báo giá/SO", readonly=True, copy=False)

    state = fields.Selection([("draft","Nháp"),("confirmed","Đã xác nhận")], default="draft", tracking=True)
    line_ids = fields.One2many("openapp.boq.line","boq_id", string="Dòng BoQ")

    amount_total = fields.Monetary("Tổng tiền", compute="_compute_amount", currency_field="currency_id", store=True)
    currency_id = fields.Many2one("res.currency", default=lambda s: s.env.company.currency_id.id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("company_id", self.env.company.id)
        return super().create(vals_list)

    def write(self, vals):
        # nếu ai đó clear company_id (hiếm), set lại để tránh lỗi report
        if "company_id" in vals and not vals["company_id"]:
            vals["company_id"] = self.env.company.id
        return super().write(vals)
    
    @api.depends("line_ids.total_price")
    def _compute_amount(self):
        for r in self:
            r.amount_total = sum(r.line_ids.mapped("total_price") or [0.0])

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})

    def action_open_sale_order(self):
        self.ensure_one()
        if not self.sale_order_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": self.sale_order_id.id,
            "target": "current",
        }

    def action_print_quotation(self):
        """Gọi report chuẩn + fallback theo report_name để tránh lỗi xmlid."""
        self.ensure_one()
        # xmlid chuẩn
        try:
            return self.env.ref(
                "openapp_erp_construction.action_report_boq_quotation"
            ).report_action(self.ids)
        except Exception:
            pass
        # fallback theo report_name
        rep = self.env["ir.actions.report"].sudo().search(
            [
                ("report_name", "=", "openapp_erp_construction.report_boq_quotation_tmpl"),
                ("model", "=", "openapp.boq"),
            ],
            limit=1,
        )
        if rep:
            return rep.report_action(self.ids)
        raise UserError(
            _(
                "Không tìm thấy report theo xmlid/report_name.\n"
                "- Kiểm tra reports/report_boq_quotation_action.xml (id='report_boq_quotation')\n"
                "- Kiểm tra reports/report_boq_quotation_templates.xml (t-name='openapp_erp_construction.report_boq_quotation_tmpl')\n"
                "- Đảm bảo 2 file đã khai trong manifest và bạn đã Upgrade module."
            )
        )

    # ---- BoQ -> Sales Order
    def action_create_sale_order(self):
        self.ensure_one()
        if not self.partner_id:
            raise ValidationError(_("Vui lòng chọn Khách hàng trước khi tạo báo giá."))

        if self.sale_order_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "sale.order",
                "view_mode": "form",
                "res_id": self.sale_order_id.id,
            }

        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "pricelist_id": self.pricelist_id.id if self.pricelist_id else False,
                "origin": self.name,
                "client_order_ref": self.name,
            }
        )

        SOL = self.env["sale.order.line"]
        for l in self.line_ids:
            # chuẩn hóa UoM: nếu khác category với product thì dùng UoM gốc của product
            uom_id = l.uom_id.id or (l.product_id and l.product_id.uom_id.id)
            if l.product_id and l.uom_id and l.uom_id.category_id != l.product_id.uom_id.category_id:
                uom_id = l.product_id.uom_id.id

            # Qty đẩy sang SO = measure_value (trọn gói = 1)
            qty = 1.0 if l.calc_method == "lump" else (l.measure_value or 0.0)

            name = l.name or (l.product_id and l.product_id.display_name) or _("Hạng mục BoQ")
            if l.group_name:
                name = f"[{l.group_name}] {name}"

            SOL.create(
                {
                    "order_id": so.id,
                    "name": name,
                    "product_id": l.product_id.id or False,
                    "product_uom": uom_id,
                    "product_uom_qty": qty,
                    "price_unit": l.price_unit or 0.0,
                }
            )

        self.sale_order_id = so.id

        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": so.id,
        }


class OpenAppBoQLine(models.Model):
    _name = "openapp.boq.line"
    _description = "Dòng BoQ"
    _order = "sequence,id"

    boq_id = fields.Many2one("openapp.boq", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer("STT", default=10)

    line_type = fields.Selection(
        [
            ("material", "Vật tư"),
            ("labor", "Nhân công"),
            ("package", "Gói"),
            ("design", "Thiết kế"),
            ("allowance", "Tạm tính"),
        ],
        string="Loại dòng",
        default="material",
    )

    group_name = fields.Char("Nhóm hiển thị")
    name = fields.Char("Diễn giải")
    product_id = fields.Many2one("product.product", string="Vật tư/Công việc")

    uom_id = fields.Many2one("uom.uom", string="ĐVT")
    product_uom_category_id = fields.Many2one(
        "uom.category", related="product_id.uom_id.category_id", store=False, readonly=True
    )

    # 3 cách tính
    calc_method = fields.Selection(
        [("qty", "Theo khối lượng"), ("area", "Theo m²"), ("lump", "Trọn gói")],
        string="Cách tính",
        default="qty",
        required=True,
    )

    # Giữ 2 field cũ cho tương thích (không hiện ở list)
    quantity = fields.Float("Khối lượng", default=1.0)
    area_ref = fields.Float("Diện tích áp dụng (m²)")

    # Field nhập duy nhất ở list (không dùng attrs trong tree)
    measure_value = fields.Float(
        string="Số đo", compute="_compute_measure_value", inverse="_inverse_measure_value", store=False
    )
    measure_label = fields.Char(string="ĐVT đo", compute="_compute_measure_label", store=False)

    price_unit = fields.Monetary("Đơn giá", currency_field="currency_id")
    include_in_print = fields.Boolean("Hiện trên báo giá", default=True)

    total_price = fields.Monetary(
        "Thành tiền", compute="_compute_total", store=True, currency_field="currency_id"
    )
    currency_id = fields.Many2one(related="boq_id.currency_id", store=True, readonly=True)

    # ===== compute/inverse dành cho measure_value =====
    @api.depends("calc_method", "quantity", "area_ref")
    def _compute_measure_value(self):
        for l in self:
            if l.calc_method == "area":
                l.measure_value = l.area_ref or 0.0
            elif l.calc_method == "lump":
                l.measure_value = 1.0
            else:
                l.measure_value = l.quantity or 0.0

    def _inverse_measure_value(self):
        for l in self:
            v = l.measure_value or 0.0
            if l.calc_method == "area":
                l.area_ref = v
            elif l.calc_method == "lump":
                l.quantity = 1.0
                l.area_ref = 0.0
            else:
                l.quantity = v

    @api.depends("calc_method", "uom_id")
    def _compute_measure_label(self):
        for l in self:
            if l.calc_method == "area":
                l.measure_label = "m²"
            elif l.calc_method == "lump":
                l.measure_label = "Gói"
            else:
                l.measure_label = l.uom_id.name or "ĐVT"

    # ===== tổng tiền dựa trên measure_value =====
    @api.depends("measure_value", "price_unit", "calc_method")
    def _compute_total(self):
        for l in self:
            base_qty = 1.0 if l.calc_method == "lump" else (l.measure_value or 0.0)
            l.total_price = base_qty * (l.price_unit or 0.0)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for l in self:
            if l.product_id:
                l.uom_id = l.product_id.uom_id.id
                if not l.price_unit:
                    l.price_unit = l.product_id.list_price or 0.0

    @api.constrains("measure_value", "price_unit")
    def _check_positive_numbers(self):
        for l in self:
            if l.calc_method != "lump" and l.measure_value is not None and l.measure_value < 0:
                raise ValidationError(_("Số đo phải >= 0."))
            if l.price_unit is not None and l.price_unit < 0:
                raise ValidationError(_("Đơn giá phải >= 0."))
