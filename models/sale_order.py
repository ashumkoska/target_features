# -*- coding: utf-8 -*-

from openerp import api, models, fields, _
from openerp.osv import osv


class sale_order(models.Model):
    
    _inherit = 'sale.order'
    
    def _get_default_payment_term(self):
        payment_term = self.env['account.payment.term'].search([('name', 'in', ['8 дена', '8 dena', '8 Дена', '8 Dena', '8 days', '8 Days'])], limit=1)
        return payment_term and payment_term.id
    
    state = fields.Selection([('draft', 'Draft Quotation'),
                              ('waiting_approval', 'Waiting Approval'),
                              ('approved', 'Approved Quotation'),
                              ('sent', 'Quotation Sent'),
                              ('cancel', 'Cancelled'),
                              ('waiting_date', 'Waiting Schedule'),
                              ('progress', 'Sales Order'),
                              ('manual', 'Sale to Invoice'),
                              ('shipping_except', 'Shipping Exception'),
                              ('invoice_except', 'Invoice Exception'),
                              ('done', 'Done')])
    second_approval = fields.Boolean(string='Show Second Approval', compute='compute_second_approval', store=True)
    discount_approved = fields.Boolean(string='Discount Approved', default=False)
    
    @api.one
    @api.depends('order_line', 'order_line.discount')
    def compute_second_approval(self):
        if any(l.discount > 20 for l in self.order_line):
            self.second_approval = True
        else:
            self.second_approval = False
            
    @api.multi
    def action_approve_quot(self):
        self.write({'state': 'approved', 'discount_approved': True})
        
    def action_quotation_send(self, cr, uid, ids, context=None):
        '''  Override to use a modified template '''
        action_dict = super(sale_order, self).action_quotation_send(cr, uid, ids, context=context)
        try:
            template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'target_features', 'sale_order_email_template_mk')[1]
            # assume context is still a dict, as prepared by super
            ctx = action_dict['context']
            ctx['default_template_id'] = template_id
            ctx['default_use_template'] = True
        except Exception:
            pass
        return action_dict
        
    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the sales order and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'quotation_sent')
        return self.pool['report'].get_action(cr, uid, ids, 'target_features.report_saleorder_target', context=context)
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        '''Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        '''
        if context is None:
            context = {}
        journal_id = self.pool['account.invoice'].default_get(cr, uid, ['journal_id'], context=context)['journal_id']
        if not journal_id:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_invoice_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order._get_default_payment_term(),
            'fiscal_position': order.fiscal_position.id or order.partner_invoice_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'section_id' : order.section_id.id
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals
        
    @api.model
    def create(self, vals):
        res = super(sale_order, self).create(vals)
        if res.second_approval and res.state == 'draft':
            res.update({'state': 'waiting_approval'})
        return res
        
    @api.multi
    def write(self, vals):
        res = super(sale_order, self).write(vals)
        for order in self:
            if order.second_approval and order.state == 'draft':
                order.update({'state': 'waiting_approval'})
        return res
