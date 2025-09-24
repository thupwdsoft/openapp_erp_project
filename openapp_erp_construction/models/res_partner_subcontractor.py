# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_subcontractor = fields.Boolean(
        string="Là Nhà thầu phụ",
        help="Đánh dấu đối tác này là Nhà thầu phụ để phân biệt với khách hàng/nhà cung cấp."
    )
    subcontract_count = fields.Integer(
        string="Hợp đồng thầu phụ",
        compute="_compute_subcontract_count",
    )

    @api.depends('is_subcontractor')
    def _compute_subcontract_count(self):
        SubContract = self.env['openapp.subcontract']
        for r in self:
            r.subcontract_count = SubContract.sudo().search_count([('partner_id', '=', r.id)]) if r.id else 0

    def action_view_subcontracts(self):
        self.ensure_one()
        action = self.env.ref('openapp_erp_construction.action_openapp_subcontract', raise_if_not_found=False)
        if action:
            act = action.read()[0]
            act['domain'] = [('partner_id', '=', self.id)]
            act['context'] = {'default_partner_id': self.id}
            return act
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hợp đồng thầu phụ'),
            'res_model': 'openapp.subcontract',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
