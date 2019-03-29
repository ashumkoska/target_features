# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class res_partner(models.Model):
    
    _inherit = 'res.partner'
    
    partner_url = fields.Char(string='Hyperlink', compute='compute_partner_url')
    is_company = fields.Boolean(default=True)
    old_notes = fields.Text(string='Old Notes')
    note_ids = fields.Many2many('partner.note', 'partner_note_rel', 'partner_id', 'note_id', string='Note')
    lang = fields.Selection(default='mk_MK')
    
    @api.one
    @api.depends('SubjectID')
    def compute_partner_url(self):
        if self.SubjectID:
            url_base = 'http://biznismreza.mk/Subjekt/Organizacija/'
            self.partner_url = '%s%s' % (url_base, self.SubjectID)
            

class partner_note(models.Model):
    
    _name = 'partner.note'
    _description = 'Partner Tag'
    
    name = fields.Char(string='Name', required=True)
    partner_ids = fields.Many2many('res.partner', 'partner_note_rel', 'note_id', 'partner_id', string='Partners')
