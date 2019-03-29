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
    expiration_sent_1 = fields.Boolean(string='Expiration Sent (1 Month)', readonly=True, copy=False)
    expiration_sent_2 = fields.Boolean(string='Expiration Sent (2 Month)', readonly=True, copy=False)
    expiration_sent_3 = fields.Boolean(string='Expiration Sent (3 Month)', readonly=True, copy=False)
    to_renew = fields.Boolean(string='To Renew', default=False)
    
    # overwriting the original function using the old api
    def onchange_recurring_invoices(self, cr, uid, ids, recurring_invoices, date_start=False, context=None):
        value = {}
        if date_start and recurring_invoices:
            next_date = fields.Datetime.from_string(date_start) + relativedelta(months=1)
            value = {'value': {'recurring_next_date': next_date}}
        return value
    
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
        all_contracts = self.search(['|', '|', ('expiration_sent_1', '=', False), ('expiration_sent_2', '=', False), ('expiration_sent_3', '=', False)])
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
                    
    @api.model
    def check_contracts_to_renew(self):
        all_contracts = self.search([])
        for contract in all_contracts:
            end_date = contract.date
            if end_date:
                two_months_after = fields.Datetime.from_string(end_date) + relativedelta(months=+2)
                three_months_before = fields.Datetime.from_string(end_date) + relativedelta(months=-3)
                if date.today() >= three_months_before.date() and date.today() <= two_months_after.date():
                    contract.write({'to_renew': True})
                elif date.today() < three_months_before.date() and date.today() > two_months_after.date() and contract.to_renew == True:
                    contract.write({'to_renew': False})
    
    # overwriting the original function using the old api         
    def _prepare_invoice_data(self, cr, uid, contract, context=None):
        values = super(account_analytic_account, self)._prepare_invoice_data(cr, uid, contract, context)
        payment_term_id = self.pool('account.payment.term').search(cr, uid, [('name', 'in', ['8 дена', '8 dena', '8 Дена', '8 Dena', '8 days', '8 Days'])], limit=1)
        payment_term = self.pool('account.payment.term').browse(cr, uid, payment_term_id, context=context)
        if payment_term:
            date_due = fields.Datetime.from_string(contract.recurring_next_date) + relativedelta(days=8)
            values.update({
                'payment_term': payment_term.id,
                'date_due': date_due
            })
        return values
    
    # overwriting the original function using the old api
    def _prepare_invoice_line(self, cr, uid, line, fiscal_position, context=None):
        values = super(account_analytic_account, self)._prepare_invoice_line(cr, uid, line, fiscal_position, context)
        values['invoice_line_tax_id'] = [(6, 0, line.tax_ids.ids)]
        return values
    
    # overwriting the original function using the old api
    def _recurring_create_invoice(self, cr, uid, ids, automatic=False, context=None):
        invoice_ids = super(account_analytic_account, self)._recurring_create_invoice(cr, uid, ids, automatic, context)
        invoices = self.pool['account.invoice'].browse(cr, uid, invoice_ids, context=context)
        for inv in invoices:
            inv.button_reset_taxes()
        return invoice_ids
    
    @api.model
    def create(self, vals):
        end_date = vals.get('date', False)
        if end_date:
            two_months_after = fields.Datetime.from_string(end_date) + relativedelta(months=+2)
            three_months_before = fields.Datetime.from_string(end_date) + relativedelta(months=-3)
            if date.today() >= three_months_before.date() and date.today() <= two_months_after.date():
                vals['to_renew'] = True
        return super(account_analytic_account, self).create(vals)
    
    @api.multi
    def write(self, vals):
        end_date = vals.get('date', False)
        if end_date:
            two_months_after = fields.Datetime.from_string(end_date) + relativedelta(months=+2)
            three_months_before = fields.Datetime.from_string(end_date) + relativedelta(months=-3)
            if date.today() >= three_months_before.date() and date.today() <= two_months_after.date():
                vals['to_renew'] = True
            elif date.today() < three_months_before.date() and date.today() > two_months_after.date():
                vals['to_renew'] = False
        return super(account_analytic_account, self).write(vals)
    

class account_analytic_invoice_line(models.Model):
    
    _inherit = 'account.analytic.invoice.line'
    
    tax_ids = fields.Many2many('account.tax', 'contract_invoice_line_tax', 'invoice_line_id', 'tax_id', string='Taxes', 
                               domain=[('parent_id', '=', False), '|', ('active', '=', False), ('active', '=', True)])
