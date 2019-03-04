# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class sale_order(models.Model):
    
    _inherit = 'sale.order'
    
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
    discount_approved = fields.Boolean(string='Discount Approved', readonly=True, default=False)
    
    @api.one
    @api.depends('order_line', 'order_line.discount')
    def compute_second_approval(self):
        if any(l.discount > 30 for l in self.order_line):
            self.second_approval = True
        else:
            self.second_approval = False
            
    @api.multi
    def action_approve_quot(self):
        self.write({'state': 'approved', 'discount_approved': True})
        
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
