# -*- coding: utf-8 -*-

from openerp import api, models, fields, _
from openerp.exceptions import RedirectWarning
from dateutil.relativedelta import relativedelta

class account_invoice(models.Model):
    
    _inherit = 'account.invoice'
    
    def _get_default_payment_term(self):
        payment_term = self.env['account.payment.term'].search([('name', 'in', ['8 дена', '8 dena', '8 Дена', '8 Dena', '8 days', '8 Days'])], limit=1)
        return payment_term and payment_term.id
    
    payment_term = fields.Many2one(default=_get_default_payment_term)
    
    @api.one
    @api.onchange('payment_term')
    def onchange_payment_term(self):
        if self.payment_term and any(self.payment_term.name == name for name in [u'8 дена', u'8 dena', u'8 Дена', u'8 Dena', u'8 days', u'8 Days']) and self.date_invoice:
            date_due = fields.Datetime.from_string(self.date_invoice) + relativedelta(months=1)
            self.date_due = date_due
    
    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False

        p = self.env['res.partner'].browse(partner_id or False)
        if partner_id:
            rec_account = p.property_account_receivable
            pay_account = p.property_account_payable
            if company_id:
                if p.property_account_receivable.company_id and \
                        p.property_account_receivable.company_id.id != company_id and \
                        p.property_account_payable.company_id and \
                        p.property_account_payable.company_id.id != company_id:
                    prop = self.env['ir.property']
                    rec_dom = [('name', '=', 'property_account_receivable'), ('company_id', '=', company_id)]
                    pay_dom = [('name', '=', 'property_account_payable'), ('company_id', '=', company_id)]
                    res_dom = [('res_id', '=', 'res.partner,%s' % partner_id)]
                    rec_prop = prop.search(rec_dom + res_dom) or prop.search(rec_dom)
                    pay_prop = prop.search(pay_dom + res_dom) or prop.search(pay_dom)
                    rec_account = rec_prop.get_by_record(rec_prop)
                    pay_account = pay_prop.get_by_record(pay_prop)
                    if not rec_account and not pay_account:
                        action = self.env.ref('account.action_account_config')
                        msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                        raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('out_invoice', 'out_refund'):
                account_id = rec_account.id
                payment_term_id = p.property_payment_term.id
            else:
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term.id
            fiscal_position = p.property_account_position.id

        result = {'value': {
            'account_id': account_id,
            # default payment_term should be 8 days
            # 'payment_term': payment_term_id,
            'fiscal_position': fiscal_position,
        }}
    
    @api.model
    def create(self, vals):
        reference = vals.get('reference', False)
        if reference:
            sale = self.env['sale.order'].search([('name', '=', reference)], limit=1)
            if vals.get('comment', '') == sale.note:
                vals['comment'] = ''
        return super(account_invoice, self).create(vals)
