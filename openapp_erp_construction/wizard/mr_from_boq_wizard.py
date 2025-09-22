from odoo import models, fields
class OpenAppMRFromBoQWizard(models.TransientModel):
    _name="openapp.mr.from.boq.wizard"; _description="Tạo MR từ BoQ"
    boq_id=fields.Many2one("openapp.boq", string="BoQ", required=True)
    project_id=fields.Many2one(related="boq_id.project_id", string="Dự án", store=False)
    line_ids=fields.One2many("openapp.mr.from.boq.wizard.line","wizard_id", string="Dòng")
    def action_create_mr(self):
        self.ensure_one()
        mr=self.env["openapp.material.request"].create({
            "project_id": self.boq_id.project_id.id,
            "line_ids": [(0,0,{"product_id":l.product_id.id,"uom_id":l.uom_id.id,"quantity":l.quantity,"description":l.name}) for l in self.line_ids if l.quantity>0],
        })
        action=self.env["ir.actions.act_window"]._for_xml_id("openapp_erp_construction.action_openapp_mr")
        action.update({"res_id":mr.id,"view_mode":"form"}); return action
class OpenAppMRFromBoQWizardLine(models.TransientModel):
    _name="openapp.mr.from.boq.wizard.line"; _description="Dòng BoQ chọn tạo MR"
    wizard_id=fields.Many2one("openapp.mr.from.boq.wizard", required=True, ondelete="cascade")
    name=fields.Char("Diễn giải"); product_id=fields.Many2one("product.product", string="Vật tư")
    uom_id=fields.Many2one("uom.uom", string="ĐVT"); quantity=fields.Float("Số lượng", default=1.0)
