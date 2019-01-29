# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class res_partner(models.Model):
    
    _inherit = 'res.partner'
    
    partner_url = fields.Char(string='Hyperlink', compute='compute_partner_url')
    
    @api.one
    @api.depends('SubjectID')
    def compute_partner_url(self):
        if self.SubjectID:
            url_base = 'http://biznismreza.mk/Subjekt/Organizacija/'
            self.partner_url = '%s%s' % (url_base, self.SubjectID)
