# -*- coding: utf-8 -*-

from openerp import api, models, fields, _
from openerp.exceptions import RedirectWarning
from dateutil.relativedelta import relativedelta
from datetime import date
from openerp.osv import osv

class account_invoice(models.Model):
    
    _inherit = 'account.invoice'
    
    def _get_default_payment_term(self):
        payment_term = self.env['account.payment.term'].search([('name', 'in', ['8 дена', '8 dena', '8 Дена', '8 Dena', '8 days', '8 Days'])], limit=1)
        return payment_term and payment_term.id
    
    def _get_default_date_due(self):
        next_day = date.today() + relativedelta(days=+8)
        return next_day
    
    payment_term = fields.Many2one(default=_get_default_payment_term)
    contract_id = fields.Many2one('account.analytic.account', string='Contract')
    date_due = fields.Date(default=_get_default_date_due)
    
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
        
        if type in ('in_invoice', 'out_refund'):
            bank_ids = p.commercial_partner_id.bank_ids
            bank_id = bank_ids[0].id if bank_ids else False
            result['value']['partner_bank_id'] = bank_id
            result['domain'] = {'partner_bank_id':  [('id', 'in', bank_ids.ids)]}

        if payment_term != payment_term_id:
            if payment_term_id:
                to_update = self.onchange_payment_term_date_invoice(payment_term_id, date_invoice)
                result['value'].update(to_update.get('value', {}))
            else:
                result['value']['date_due'] = False

        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(bank_id)
            result['value'].update(to_update.get('value', {}))

        return result
    
        
    @api.multi
    def onchange_payment_term_date_invoice(self, payment_term_id, date_invoice):
        if not date_invoice:
            date_invoice = fields.Date.context_today(self)
        # To make sure the invoice due date should contain due date which is
        # entered by user when there is no payment term defined
        return {'value': {'date_due': self.date_due or date_invoice}}
    
    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])

        result = []
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            val = inv_line_obj.product_id_change(cr, uid, [], wizard.product_id.id,
                    False, partner_id=sale.partner_id.id, fposition_id=sale.fiscal_position.id,
                    company_id=sale.company_id.id)
            res = val['value']

            # determine and check income account
            if not wizard.product_id.id :
                prop = ir_property_obj.get(cr, uid,
                            'property_account_income_categ', 'product.category', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, sale.fiscal_position or False, prop_id)
                if not account_id:
                    raise osv.except_osv(_('Configuration Error!'),
                            _('There is no income account defined as global property.'))
                res['account_id'] = account_id
            if not res.get('account_id'):
                raise osv.except_osv(_('Configuration Error!'),
                        _('There is no income account defined for this product: "%s" (id:%d).') % \
                            (wizard.product_id.name, wizard.product_id.id,))

            # determine invoice amount
            if wizard.amount <= 0.00:
                raise osv.except_osv(_('Incorrect Data'),
                    _('The value of Advance Amount must be positive.'))
            if wizard.advance_payment_method == 'percentage':
                inv_amount = sale.amount_untaxed * wizard.amount / 100
                if not res.get('name'):
                    res['name'] = self._translate_advance(cr, uid, percentage=True, context=dict(context, lang=sale.partner_id.lang)) % (wizard.amount)
            else:
                inv_amount = wizard.amount
                if not res.get('name'):
                    #TODO: should find a way to call formatLang() from rml_parse
                    symbol = sale.pricelist_id.currency_id.symbol
                    if sale.pricelist_id.currency_id.position == 'after':
                        symbol_order = (inv_amount, symbol)
                    else:
                        symbol_order = (symbol, inv_amount)
                    res['name'] = self._translate_advance(cr, uid, context=dict(context, lang=sale.partner_id.lang)) % symbol_order

            # determine taxes
            if res.get('invoice_line_tax_id'):
                res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
            else:
                res['invoice_line_tax_id'] = False

            # create the invoice
            inv_line_values = {
                'name': res.get('name'),
                'origin': sale.name,
                'account_id': res['account_id'],
                'price_unit': inv_amount,
                'quantity': wizard.qtty or 1.0,
                'discount': False,
                'uos_id': res.get('uos_id', False),
                'product_id': wizard.product_id.id,
                'invoice_line_tax_id': res.get('invoice_line_tax_id'),
                'account_analytic_id': sale.project_id.id or False,
            }
            inv_values = {
                'name': sale.client_order_ref or sale.name,
                'origin': sale.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': sale.partner_id.property_account_receivable.id,
                'partner_id': sale.partner_invoice_id.id,
                'invoice_line': [(0, 0, inv_line_values)],
                'currency_id': sale.pricelist_id.currency_id.id,
                'comment': sale.note,
                # 'payment_term': sale.payment_term.id,
                'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id,
                'section_id': sale.section_id.id,
            }
            result.append((sale.id, inv_values))
        return result
    
    @api.multi
    def invoice_print(self):
        ''' Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow.
        '''
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        self.sent = True
        return self.env['report'].get_action(self, 'target_features.report_invoice_target')
    
    def action_invoice_sent(self, cr, uid, ids, context=None):
        '''  Override to use a modified template '''
        action_dict = super(account_invoice, self).action_invoice_sent(cr, uid, ids, context=context)
        try:
            template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'target_features', 'account_invoice_email_template_mk')[1]
            # assume context is still a dict, as prepared by super
            ctx = action_dict['context']
            ctx['default_template_id'] = template_id
            ctx['default_use_template'] = True
        except Exception:
            pass
        return action_dict

    
    @api.model
    def create(self, vals):
        reference = vals.get('reference', False)
        if reference:
            sale = self.env['sale.order'].search([('name', '=', reference)], limit=1)
            if vals.get('comment', '') == sale.note:
                vals['comment'] = ''
        return super(account_invoice, self).create(vals)
