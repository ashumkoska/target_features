# -*- coding: utf-8 -*-

import re
from openerp import api, models, fields, _
from openerp.exceptions import ValidationError

HTML_ENTITIES = {
    '&nbsp;': ' ',
    '&lt;': '<',
    '&gt;': '>',
    '&amp;': '&',
    '&quot;': '"',
    '&apos;': '\'',
    '&cent;': '¢',
    '&pound;': '£',
    '&yen;': '¥',
    '&euro;': '€',
    '&copy;': '©',
    '&reg;': '®'    
}

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    for key, value in HTML_ENTITIES.iteritems():
        cleantext = re.sub(key, value, cleantext)
    return cleantext.strip()


class user_type_wiz(models.TransientModel):

    _name = 'user.type.wiz'
    _description = 'User Type Wizard'

    user_type = fields.Selection([('prepaid', 'Prepaid User'),
                                  ('package', 'Package User')], string='Type of User')
    email_template_id = fields.Many2one('email.template', string='Template')
    email_body = fields.Html(string='Body')
    contract_id = fields.Many2one('account.analytic.account', string='Contract', readonly=True)
    
    @api.onchange('user_type')
    def onchange_user_type(self):
        template = False
        if self.user_type == 'prepaid':
            template = self.env.ref('target_features.mail_prepaid_activation_notif')
        elif self.user_type == 'package':
            template = self.env.ref('target_features.mail_package_activation_notif')
        if template:
            self.email_template_id = template
            self.email_body = template.body_html
        else:
            self.email_template_id = False
            self.email_body = False
    
    @api.one
    def send_email(self):
        if not self.contract_id.username:
            raise ValidationError(_('Please enter a username.'))
        elif not self.contract_id.password:
            raise ValidationError(_('Please enter a password.'))
        if cleanhtml(self.email_body) != cleanhtml(self.email_template_id.body_html):
            self.email_template_id.write({'body_html': self.email_body})
        self.email_template_id.send_mail(self.contract_id.id)
