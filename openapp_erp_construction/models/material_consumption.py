# -*- coding: utf-8 -*-
from odoo import models, fields

class MaterialConsumption(models.Model):
    _name = "openapp.material.consumption"
    _description = "Material Consumption by Project/Site"
    _auto = False

    project_id = fields.Many2one("project.project", string="Công trình", readonly=True)
    mr_id = fields.Many2one("openapp.material.request", string="MR", readonly=True)
    date = fields.Datetime("Ngày xuất", readonly=True)
    product_id = fields.Many2one("product.product", string="Sản phẩm", readonly=True)
    qty_done = fields.Float("SL đã xuất (theo ĐVT SP)", readonly=True)
    uom_id = fields.Many2one("uom.uom", string="ĐVT SP", readonly=True)

    @property
    def _table_query(self):
        # Quy đổi về uom của product template (pt.uom_id)
        return """
            SELECT
                MIN(sml.id) AS id,
                sp.openapp_mr_id AS mr_id,
                mr.project_id AS project_id,
                sp.date_done AS date,
                sml.product_id AS product_id,
                pt.uom_id AS uom_id,
                SUM(
                    CASE
                        WHEN ufrom.category_id = uto.category_id
                             AND ufrom.factor > 0 AND uto.factor > 0
                        THEN sml.quantity * (ufrom.factor / uto.factor)
                        ELSE sml.quantity
                    END
                ) AS qty_done
            FROM stock_move_line sml
            JOIN stock_move sm
              ON sm.id = sml.move_id
            JOIN stock_picking sp
              ON sp.id = sm.picking_id
            JOIN stock_picking_type spt
              ON spt.id = sp.picking_type_id
            JOIN openapp_material_request mr
              ON mr.id = sp.openapp_mr_id
            JOIN product_product pp
              ON pp.id = sml.product_id
            JOIN product_template pt
              ON pt.id = pp.product_tmpl_id
            JOIN uom_uom ufrom
              ON ufrom.id = sml.product_uom_id
            JOIN uom_uom uto
              ON uto.id = pt.uom_id
            WHERE sp.state = 'done'
              AND spt.code = 'outgoing'
            GROUP BY sp.openapp_mr_id, mr.project_id, sp.date_done, sml.product_id, pt.uom_id
        """

    def init(self):
        self._cr.execute(f"DROP VIEW IF EXISTS {self._table}")
        self._cr.execute(f"CREATE OR REPLACE VIEW {self._table} AS ({self._table_query})")
