# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class sale_order(models.Model):
    
    _inherit = 'sale.order'
    
    state = fields.Selection([('draft', 'Draft Quotation'),
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
    
    @api.one
    @api.depends('order_line', 'order_line.discount')
    def compute_second_approval(self):
        if any(l.discount > 30 for l in self.order_line):
            self.second_approval = True
        else:
            self.second_approval = False
            
    @api.multi
    def action_approve_quot(self):
        self.write({'state': 'approved'})
