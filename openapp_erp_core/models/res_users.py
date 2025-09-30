# models/res_users.py
from odoo import api, models # type: ignore

class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        # Ví dụ: nếu cần tự gán nhóm Sales (tuỳ context)
        if self.env.context.get("openapp_sales_user"):
            grp = self.env.ref("sales_team.group_sale_salesman", raise_if_not_found=False)
            if grp:
                for user in users:
                    user.write({"groups_id": [(4, grp.id)]})
        return users
