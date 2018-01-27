from odoo import models, api
from .. import wkf_engine


class WorkflowMixIn(models.AbstractModel):
    _name = 'workflow.mixin'

    @api.multi
    def create_workflow(self):
        """ Create a workflow instance for the given records. """
        for res_id in self.ids:
            wkf_engine.trg_create(self._uid, self._name, res_id, self._cr)
        return True

    @api.multi
    def delete_workflow(self):
        """ Delete the workflow instances bound to the given records. """
        for res_id in self.ids:
            wkf_engine.trg_delete(self._uid, self._name, res_id, self._cr)
        self.invalidate_cache()
        return True

    @api.multi
    def step_workflow(self):
        """ Reevaluate the workflow instances of the given records. """
        for res_id in self.ids:
            wkf_engine.trg_write(self._uid, self._name, res_id, self._cr)
        return True

    @api.multi
    def signal_workflow(self, signal):
        """ Send the workflow signal, and return a dict mapping ids to workflow results. """
        result = {}
        for res_id in self.ids:
            result[res_id] = wkf_engine.trg_validate(self._uid, self._name, res_id, signal, self._cr)
        return result

    @api.model
    def redirect_workflow(self, old_new_ids):
        """ Rebind the workflow instance bound to the given 'old' record IDs to
            the given 'new' IDs. (``old_new_ids`` is a list of pairs ``(old, new)``.
        """
        for old_id, new_id in old_new_ids:
            wkf_engine.trg_redirect(self._uid, self._name, old_id, new_id, self._cr)
        self.invalidate_cache()
        return True

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        new_record = super().create(vals)
        new_record.create_workflow()
        return new_record

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        self.step_workflow()
        return res

    @api.multi
    def unlink(self):
        self.delete_workflow()
        return super().unlink()

