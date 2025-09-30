from odoo import models, fields, api
import base64
from odoo.tools.misc import file_open


class ProductCategory(models.Model):
    _inherit = 'product.category'

    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)

    @api.model
    def _default_image(self):
        return base64.b64encode(file_open('lunch/static/img/lunch.png', 'rb').read())