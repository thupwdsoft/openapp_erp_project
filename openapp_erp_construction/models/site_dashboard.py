# -*- coding: utf-8 -*-
from odoo import models, fields, api

STATES_OPEN = ('confirmed', 'assigned', 'waiting', 'partially_available')

class OpenAppSiteDashboard(models.TransientModel):
    _name = "openapp.site.dashboard"
    _description = "Tổng quan công trình (Kho)"

    receipt_open = fields.Integer(compute="_compute_all")
    receipt_late = fields.Integer(compute="_compute_all")
    receipt_working = fields.Integer(compute="_compute_all")

    delivery_open = fields.Integer(compute="_compute_all")
    delivery_late = fields.Integer(compute="_compute_all")
    delivery_working = fields.Integer(compute="_compute_all")

    def _domain_base(self):
        # Liên quan MR hoặc đơn thuần lọc theo loại phiếu
        return ['|', ('openapp_mr_id', '!=', False), ('id', '!=', 0)]

    def _compute_all(self):
        Picking = self.env['stock.picking'].sudo()
        now = fields.Datetime.now()

        rec_domain = [('picking_type_id.code', '=', 'incoming'),
                      ('state', 'not in', ('done', 'cancel'))] + self._domain_base()
        self.receipt_open = Picking.search_count(rec_domain)
        self.receipt_late = Picking.search_count(rec_domain + [('scheduled_date', '<', now)])
        self.receipt_working = Picking.search_count(rec_domain + [('state', 'in', STATES_OPEN)])

        del_domain = [('picking_type_id.code', '=', 'outgoing'),
                      ('state', 'not in', ('done', 'cancel'))] + self._domain_base()
        self.delivery_open = Picking.search_count(del_domain)
        self.delivery_late = Picking.search_count(del_domain + [('scheduled_date', '<', now)])
        self.delivery_working = Picking.search_count(del_domain + [('state', 'in', STATES_OPEN)])

    # ==== mở danh sách đã lọc ====
    def _open_picking(self, base_domain):
        return {
            'type': 'ir.actions.act_window',
            'name': "Phiếu kho",
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': base_domain,
        }

    def action_open_receipts(self):
        return self._open_picking([('picking_type_id.code', '=', 'incoming'),
                                   ('state', 'not in', ('done', 'cancel'))] + self._domain_base())

    def action_open_deliveries(self):
        return self._open_picking([('picking_type_id.code', '=', 'outgoing'),
                                   ('state', 'not in', ('done', 'cancel'))] + self._domain_base())

    # tiện ích để menu mở 1 record duy nhất
    @api.model
    def action_open_dashboard(self):
        rec = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': "Tổng quan công trình",
            'res_model': 'openapp.site.dashboard',
            'res_id': rec.id,
            'view_mode': 'kanban',
            'target': 'current',
        }
