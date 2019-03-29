# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class mail_mail(models.Model):
    
    _inherit = 'mail.mail'
    
    body_c_html = fields.Html(string='Body', compute='compute_body_c_html', store=True, readonly=True)
    
    @api.one
    @api.depends('body_html')
    def compute_body_c_html(self):
        self.body_c_html = self.body_html