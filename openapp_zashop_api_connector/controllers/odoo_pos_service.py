from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import calendar


class POSReportController(http.Controller):

    @http.route('/zalo/shop/api/v1/pos-report', auth='public', type='json', methods=['POST'], csrf=False)
    def get_pos_summary_report(self, **kwargs):
        api_key = request.httprequest.headers.get('X-API-KEY')
        expected_key = 'odoo-pos-report-KEY@2025!XxSd98123'
        if api_key != expected_key:
            return {'status': 'error', 'message': 'Invalid API Key'}, 401
        
        today = datetime.today()
        start_day = datetime.combine(today.date(), datetime.min.time())
        end_day = datetime.combine(today.date(), datetime.max.time())

        start_week = start_day - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

        start_month = datetime(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_month = datetime(today.year, today.month, last_day, 23, 59, 59)

        return {
            'status': 'success',
            'date': today.strftime('%Y-%m-%d'),
            'report': {
                'today': self._get_report(start_day, end_day),
                'week': self._get_report(start_week, end_week),
                'month': self._get_report(start_month, end_month)
            }
        }

    def _get_report(self, start_date, end_date):
        pos_orders = request.env['pos.order'].sudo().search([
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('state', 'in', ['paid', 'done', 'invoiced'])
        ])

        summary = {
            'total_orders': len(pos_orders),
            'total_amount': sum(order.amount_total for order in pos_orders),
            'products': {}
        }

        for order in pos_orders:
            for line in order.lines:
                product = line.product_id.display_name
                if product not in summary['products']:
                    summary['products'][product] = {'qty': 0, 'amount': 0.0}
                summary['products'][product]['qty'] += line.qty
                summary['products'][product]['amount'] += line.price_subtotal

        return summary

