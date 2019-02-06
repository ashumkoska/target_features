# -*- coding: utf-8 -*-

from openerp import api, models, fields, _
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp.exceptions import ValidationError


class account_analytic_account(models.Model):
    
    _inherit = 'account.analytic.account'
    
    username = fields.Char(string='Username')
    password = fields.Char(string='Password')
    state = fields.Selection([('template', 'Template'),
                              ('draft', 'New'),
                              ('open', 'In Progress'),
                              ('pending', 'To Renew'),
                              ('sent', 'Email Sent'),
                              ('close', 'Closed'),
                              ('cancelled', 'Cancelled')])
    expiration_sent_1 = fields.Boolean(string='Expiration Sent (1 Month)', readonly=True)
    expiration_sent_2 = fields.Boolean(string='Expiration Sent (2 Month)', readonly=True)
    expiration_sent_3 = fields.Boolean(string='Expiration Sent (3 Month)', readonly=True)
    
    @api.multi
    def send_activation_mail(self):
        self.ensure_one()
        if not self.username:
            raise ValidationError(_('Please enter a username.'))
        elif not self.password:
            raise ValidationError(_('Please enter a password.'))
        return {            
            'name': _('Type of User'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'user.type.wiz',
            'target': 'new',
            'context': {'default_contract_id': self.id}
        }
    
    @api.model
    def check_expired_contracts(self):
        all_contracts = self.search([])
        for contract in all_contracts:
            end_date = contract.date
            if end_date:                
                one_month_adv = fields.Datetime.from_string(end_date) + relativedelta(months=-1)
                two_months_adv = fields.Datetime.from_string(end_date) + relativedelta(months=-2)
                three_months_adv = fields.Datetime.from_string(end_date) + relativedelta(months=-3)
                template = False
                
                if date.today() == one_month_adv.date() and not contract.expiration_sent_1:
                    template = self.env.ref('target_features.mail_contract_expiration_1')
                    contract.write({'expiration_sent_1': True})
                elif date.today() == two_months_adv.date() and not contract.expiration_sent_2:
                    template = self.env.ref('target_features.mail_contract_expiration_2')
                    contract.write({'expiration_sent_2': True})
                elif date.today() == three_months_adv.date() and not contract.expiration_sent_3:
                    template = self.env.ref('target_features.mail_contract_expiration_3')
                    contract.write({'expiration_sent_3': True})                
                
                if template:
                    template.send_mail(contract.id)
                    