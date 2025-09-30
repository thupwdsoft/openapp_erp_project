from odoo import http
from odoo.http import request

class ZaloVerificationController(http.Controller):
    @http.route('/callback', type='http', auth='public', website=True, csrf=False)
    def zalo_site_verification(self, **kwargs):
        html_content = """
        <!DOCTYPE html>
        <html lang="en">

        <head>
            <meta property="zalo-platform-site-verification" content="SjM4CuBn2cbppuTeyRyBTo-1fbN3ztSACZ8q" />
        </head>

        <body>
        There Is No Limit To What You Can Accomplish Using Zalo!
        </body>

        </html>
        """
        return request.make_response(html_content, headers=[('Content-Type', 'text/html')])
