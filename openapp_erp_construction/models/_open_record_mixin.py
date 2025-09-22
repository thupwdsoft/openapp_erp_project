from odoo import models # type: ignore
class OpenRecordActionMixin(models.AbstractModel):
    _name = "openapp.open_record_action_mixin"
    _description = "Open safely record(s)"

    
    def _action_open_records(self, model, records, name=None, form_view_xmlid=None):
        recs = records.exists()
        action = {"type":"ir.actions.act_window","res_model":model,"target":"current"}
        if name: action["name"]=name
        if len(recs)==1:
            action.update({"view_mode":"form","res_id":recs.id})
            if form_view_xmlid:
                view = self.env.ref(form_view_xmlid, raise_if_not_found=False)
                if view: action["views"]=[(view.id,"form")]
        else:
            action.update({"view_mode":"list,form","domain":[("id","in",recs.ids or [0])]})
            action.pop("res_id",None)
        return action
