# -*- coding: utf-8 -*-
from odoo import models, fields

class JobCostingLine(models.Model):
    _name = "openapp.job.costing.line"
    _description = "Chi phí công trình (từ kho)"
    _auto = False

    project_id = fields.Many2one("project.project", string="Công trình", readonly=True)
    mr_id      = fields.Many2one("openapp.material.request", string="MR", readonly=True)
    date       = fields.Date("Ngày", readonly=True)
    product_id = fields.Many2one("product.product", string="Vật tư", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Đối tác", readonly=True)
    name       = fields.Char("Mô tả", readonly=True)

    # value trên SVL là giá vốn (âm khi xuất). Quy ước: amount = -SUM(value) (chi phí dương)
    debit  = fields.Monetary("Nợ", currency_field="currency_id", readonly=True)
    credit = fields.Monetary("Có",  currency_field="currency_id", readonly=True)
    amount = fields.Monetary("Số tiền (+ chi phí / - hoàn nhập)", currency_field="currency_id", readonly=True)

    currency_id = fields.Many2one(
        "res.currency", string="Tiền tệ",
        default=lambda s: s.env.company.currency_id.id, readonly=True
    )

    @property
    def _table_query(self):
        return """
            WITH rows AS (
                SELECT
                    svl.id,
                    mr.project_id                 AS project_id,
                    sp.openapp_mr_id              AS mr_id,
                    COALESCE(svl.create_date::date, sm.date::date) AS move_date,
                    svl.product_id                AS product_id,
                    sp.partner_id                 AS partner_id,
                    COALESCE(sp.name, sm.reference, 'Xuất kho MR') AS label,
                    svl.value                     AS svl_value,
                    rc.currency_id                AS currency_id
                FROM stock_valuation_layer svl
                JOIN stock_move       sm  ON sm.id = svl.stock_move_id
                JOIN stock_picking    sp  ON sp.id = sm.picking_id
                JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                JOIN openapp_material_request mr ON mr.id = sp.openapp_mr_id
                JOIN res_company rc ON rc.id = sp.company_id
                WHERE sp.state = 'done'
                  AND spt.code = 'outgoing'
            )
            SELECT
                MIN(id)                          AS id,
                project_id,
                mr_id,
                move_date                         AS date,
                product_id,
                partner_id,
                label                              AS name,
                CASE WHEN -SUM(svl_value) > 0 THEN ROUND(-SUM(svl_value), 2) ELSE 0 END AS debit,
                CASE WHEN -SUM(svl_value) < 0 THEN ROUND( SUM(svl_value), 2) ELSE 0 END AS credit,
                ROUND(-SUM(svl_value), 2)         AS amount,
                currency_id
            FROM rows
            GROUP BY project_id, mr_id, move_date, product_id, partner_id, label, currency_id
        """

    def init(self):
        self._cr.execute(f"DROP VIEW IF EXISTS {self._table}")
        self._cr.execute(f"CREATE OR REPLACE VIEW {self._table} AS ({self._table_query})")
