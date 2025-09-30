# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class WarrantyPortal(http.Controller):

    # Form tra cứu
    @http.route('/warranty/lookup', type='http', auth='public', website=True)
    def warranty_lookup(self, **kw):
        return request.render('openapp_warranty.tmpl_warranty_lookup_form', {})

    # Xử lý form
    @http.route('/warranty/lookup/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def warranty_lookup_submit(self, **post):
        name = (post.get('code') or '').strip()
        phone = (post.get('phone') or '').strip()
        serial = (post.get('serial') or '').strip()

        dom = []
        if name:
            dom += [('name', '=', name)]
        if phone:
            dom = dom + (['|', ('partner_phone', 'ilike', phone), ('partner_id.phone', 'ilike', phone)] if dom else
                         ['|', ('partner_phone', 'ilike', phone), ('partner_id.phone', 'ilike', phone)])
        if serial:
            dom = dom + (['|', ('lot_id.name', '=', serial), ('lot_id.name', 'ilike', serial)] if dom else
                         ['|', ('lot_id.name', '=', serial), ('lot_id.name', 'ilike', serial)])

        cards = request.env['warranty.card'].sudo().search(dom or [], limit=20, order="create_date desc")
        return request.render('openapp_warranty.tmpl_warranty_lookup_result', {
            'cards': cards,
        })

    # Trang xem chi tiết bằng token (dán QR)
    @http.route(['/w/<string:token>', '/warranty/track/<string:token>'],
                type='http', auth='public', website=True)
    def warranty_track(self, token=None, **kw):
        card = request.env['warranty.card'].sudo().search([('access_token', '=', token)], limit=1)
        if not card:
            return request.not_found()
        tickets = request.env['helpdesk.ticket'].sudo().search(
            [('warranty_card_id', '=', card.id)], limit=5, order='create_date desc'
        )
        latest = tickets[:1]
        return request.render('openapp_warranty.tmpl_warranty_public', {
            'card': card,
            'tickets': tickets,
            'latest': latest and latest[0] or False,
        })
