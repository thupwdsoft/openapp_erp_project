# -*- coding: utf-8 -*-
from odoo import models, fields, api # type: ignore

class ConstructionDashboard(models.TransientModel):
    _name = "openapp.construction.dashboard"
    _description = "Construction Dashboard (Simple KPIs)"

    kpi_projects = fields.Integer("Số dự án", compute="_compute_kpis")
    kpi_open_mr = fields.Integer("MR đang mở", compute="_compute_kpis")
    kpi_rfi_open = fields.Integer("RFI mở", compute="_compute_kpis")
    kpi_ncr_open = fields.Integer("NCR mở", compute="_compute_kpis")
    kpi_wc_invoiced = fields.Integer("WC đã lập hóa đơn", compute="_compute_kpis")

    def _compute_kpis(self):
        Project = self.env["project.project"]
        MR = self.env["openapp.material.request"]
        RFI = self.env["openapp.rfi"]
        NCR = self.env["openapp.ncr"]
        WC = self.env["openapp.work.certificate"]
        for r in self:
            r.kpi_projects = Project.search_count([])
            r.kpi_open_mr = MR.search_count([('state','in',['draft','confirmed'])])
            r.kpi_rfi_open = RFI.search_count([('state','in',['draft','submitted'])])
            r.kpi_ncr_open = NCR.search_count([('state','in',['draft','submitted'])])
            r.kpi_wc_invoiced = WC.search_count([('state','=','invoiced')])
