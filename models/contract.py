# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


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
    
    @api.model
    def check_expired_contracts(self):
        pass
