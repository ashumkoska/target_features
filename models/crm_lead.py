# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class crm_lead(models.Model):
    
    _inherit = 'crm.lead'
    
    source_readonly = fields.Boolean(string='Source Readonly', default=False)
    
    @api.model
    def create(self, vals):
        if vals.get('source_id'):
            vals['source_readonly'] = True
        return super(crm_lead, self).create(vals)
    
    @api.multi
    def write(self, vals):
        if vals.get('source_id'):
            vals['source_readonly'] = True
        return super(crm_lead, self).write(vals)
    

class crm_case_stage(models.Model):
    
    _inherit = 'crm.case.stage'
    
    farmer_visible = fields.Boolean(string='Visible for users of the role Farmer', default=False)
