from odoo import models, fields

class BannerSlide(models.Model):
    _name = 'banner.slide'
    _description = 'Banner Slide'

    name = fields.Char(string='Name', required=True)
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    url = fields.Char(string='Redirect URL', help='Link to redirect when clicking the banner')
    sequence = fields.Integer(string='Sequence', default=10, help='Determines the order of the banners')
    is_active = fields.Boolean(string='Active', default=True, help='If unchecked, the banner will not be displayed.')
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        required=True, 
        default=lambda self: self.env.company,
        help='The company this banner belongs to.'
    )

    def toggle_active(self):
        """Toggle the active state of the banner."""
        for record in self:
            record.is_active = not record.is_active
