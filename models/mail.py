# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID
from openerp import api, models, fields, _


class mail_mail(models.Model):
    
    _inherit = 'mail.mail'
    
    body_c_html = fields.Html(string='Body', compute='compute_body_c_html', store=True, readonly=True)
    
    @api.one
    @api.depends('body_html')
    def compute_body_c_html(self):
        self.body_c_html = self.body_html
        
    def _get_partner_access_link(self, cr, uid, mail, partner=None, context=None):
        ''' Generate URLs for links in mails:
            - partner is not an user: signup_url
            - partner is an user: fallback on classic URL
        '''
        if context is None:
            context = {}
        if partner and not partner.user_ids:
            return ''
        else:
            return super(mail_mail, self)._get_partner_access_link(cr, uid, mail, partner=partner, context=context)