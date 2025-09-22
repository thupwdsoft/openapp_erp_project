from odoo import models, fields # type: ignore


STATE_B=[
    ("draft","Nháp"),
    ("submitted","Đã gửi"),
    ("approved","Phê duyệt"),
    ("closed","Đóng")
    ]

class RFI(models.Model):
    _name="openapp.rfi"
    _description="RFI - Yêu cầu thông tin"
    _order="id desc"

    name=fields.Char("Số RFI", default=lambda s:s.env['ir.sequence'].next_by_code('openapp.rfi'), required=True)
    project_id=fields.Many2one("project.project", string="Dự án", required=True)
    requested_by=fields.Many2one("res.users", string="Người yêu cầu")
    description=fields.Text("Mô tả / Câu hỏi")
    answer=fields.Text("Trả lời")
    date=fields.Date("Ngày", default=fields.Date.context_today)
    state=fields.Selection(STATE_B, default="draft", tracking=True)
    attachment_ids=fields.Many2many("ir.attachment", string="Đính kèm")
    
    def action_submit(self): self.write({"state":"submitted"})
    def action_approve(self): self.write({"state":"approved"})
    def action_close(self): self.write({"state":"closed"})


class NCR(models.Model):
    _name="openapp.ncr"
    _description="NCR - Biên bản không phù hợp"
    _order="id desc"

    name=fields.Char("Số NCR", default=lambda s:s.env['ir.sequence'].next_by_code('openapp.ncr'), required=True)
    project_id=fields.Many2one("project.project", string="Dự án", required=True)
    reported_by=fields.Many2one("res.users", string="Người báo cáo")
    description=fields.Text("Mô tả sai lệch")
    corrective_action=fields.Text("Hành động khắc phục")
    date=fields.Date("Ngày", default=fields.Date.context_today)
    state=fields.Selection(STATE_B, default="draft", tracking=True)
    attachment_ids=fields.Many2many("ir.attachment", string="Đính kèm")

    def action_submit(self): self.write({"state":"submitted"})
    def action_approve(self): self.write({"state":"approved"})
    def action_close(self): self.write({"state":"closed"})


class ITP(models.Model):
    _name="openapp.itp"
    _description="ITP - Kế hoạch kiểm tra & thử nghiệm" 
    _order="id desc"


    name=fields.Char("Số ITP", default=lambda s:s.env['ir.sequence'].next_by_code('openapp.itp'), required=True)
    project_id=fields.Many2one("project.project", string="Dự án", required=True)
    description=fields.Text("Mô tả / Hạng mục kiểm tra")
    date=fields.Date("Ngày", default=fields.Date.context_today)
    state=fields.Selection(STATE_B, default="draft", tracking=True)
    attachment_ids=fields.Many2many("ir.attachment", string="Đính kèm")

    def action_submit(self): self.write({"state":"submitted"})
    def action_approve(self): self.write({"state":"approved"})
    def action_close(self): self.write({"state":"closed"})
