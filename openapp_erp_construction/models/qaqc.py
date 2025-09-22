from odoo import models, fields # type: ignore

class RFI(models.Model):
    _name = "openapp.rfi"
    _description = "Yêu cầu thông tin (RFI)"

    name = fields.Char(string="Số RFI", default=lambda s: s.env['ir.sequence'].next_by_code('openapp.rfi'), readonly=True)
    project_id = fields.Many2one('project.project', string="Dự án", required=True)
    date = fields.Date(string="Ngày")
    requested_by = fields.Many2one('res.users', string='Người yêu cầu')
    description = fields.Text(string="Mô tả")
    answer = fields.Text(string="Trả lời")
    attachment_ids = fields.Many2many('ir.attachment', string='Tệp đính kèm')
    state = fields.Selection([('draft','Nháp'),('submitted','Đã gửi'),('approved','Đã duyệt'),('closed','Đã đóng')], string="Trạng thái", default='draft')
    def action_submit(self): self.write({'state': 'submitted'})
    def action_approve(self): self.write({'state': 'approved'})
    def action_close(self): self.write({'state': 'closed'})

class NCR(models.Model):
    _name = "openapp.ncr"
    _description = "Biên bản không phù hợp (NCR)"

    name = fields.Char(string="Số NCR", default=lambda s: s.env['ir.sequence'].next_by_code('openapp.ncr'), readonly=True)
    project_id = fields.Many2one('project.project', string="Dự án", required=True)
    date = fields.Date(string="Ngày")
    reported_by = fields.Many2one('res.users', string='Người báo cáo')
    description = fields.Text(string="Mô tả")
    corrective_action = fields.Text(string="Hành động khắc phục")
    attachment_ids = fields.Many2many('ir.attachment', string='Tệp đính kèm')
    state = fields.Selection([('draft','Nháp'),('submitted','Đã gửi'),('approved','Đã duyệt'),('closed','Đã đóng')], string="Trạng thái", default='draft')
    def action_submit(self): self.write({'state': 'submitted'})
    def action_approve(self): self.write({'state': 'approved'})
    def action_close(self): self.write({'state': 'closed'})

class ITP(models.Model):
    _name = "openapp.itp"
    _description = "Kế hoạch kiểm tra & thử nghiệm (ITP)"

    name = fields.Char(string="Số ITP", default=lambda s: s.env['ir.sequence'].next_by_code('openapp.itp'), readonly=True)
    project_id = fields.Many2one('project.project', string="Dự án", required=True)
    date = fields.Date(string="Ngày")
    description = fields.Text(string="Mô tả")
    attachment_ids = fields.Many2many('ir.attachment', string='Tệp đính kèm')
    state = fields.Selection([('draft','Nháp'),('submitted','Đã gửi'),('approved','Đã duyệt'),('closed','Đã đóng')], string="Trạng thái", default='draft')
    def action_submit(self): self.write({'state': 'submitted'})
    def action_approve(self): self.write({'state': 'approved'})
    def action_close(self): self.write({'state': 'closed'})
