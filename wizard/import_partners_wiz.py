# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class import_partners_wiz(models.TransientModel):

    _name = 'import.partners.wiz'
    _description = 'Import Partners Wizard'
    
    partners_file = fields.Binary(string='File')
    
    @api.multi
    def import_partners(self):        
        pass
