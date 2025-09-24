from . import boq
from . import inherit_stock
from . import material_request
from . import material_consumption
from . import res_partner_subcontractor
from . import subcontract
from . import progress_billing
#from . import variation_order
from . import qa_qc
from . import dashboard
from . import _open_record_mixin
from . import res_config_settings

# ⬇️ đưa lên trước để tạo cột project_project.analytic_account_id
from . import res_project_inherit

from . import res_task_documents_inherit
from . import site_timesheet

# Retention
from . import res_company_retention
from . import retention

# cuối cùng mới tới các view SQL phụ thuộc schema
from . import job_costing

from . import site_dashboard
