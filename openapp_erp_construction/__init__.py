from . import models
from . import wizard

def post_init_create_project_analytic(cr, registry):
    """Tạo analytic account cho các project đã tồn tại nhưng chưa có liên kết."""
    from odoo.api import Environment # type: ignore
    env = Environment(cr, 1, {})  # admin
    Project = env["project.project"].with_context(active_test=False)
    for p in Project.search([("analytic_account_id","=",False)]):
        aa = env["account.analytic.account"].create({
            "name": p.name or f"Project {p.id}",
            "company_id": p.company_id.id,
        })
        p.analytic_account_id = aa.id
