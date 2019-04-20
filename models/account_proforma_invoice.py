# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class account_proforma_invoice(models.Model):
    
    _inherit = 'account.proforma.invoice'
    
    state = fields.Selection([('draft','Draft'),
                              ('waiting_approval', 'Waiting Approval'),
                              ('approved', 'Approved Pro-Forma'),
                              ('open','Open'),
                              ('paid','Paid'),
                              ('cancel','Cancelled'),
                              ('invoiced', 'Invoiced')])
    second_approval = fields.Boolean(string='Show Second Approval', compute='compute_second_approval', store=True)
    discount_approved = fields.Boolean(string='Discount Approved', readonly=True, default=False)
    
    @api.one
    @api.depends('proforma_line', 'proforma_line.discount')
    def compute_second_approval(self):
        if any(l.discount > 20 for l in self.proforma_line):
            self.second_approval = True
        else:
            self.second_approval = False
            
    @api.multi
    def action_approve_proforma(self):
        self.write({'state': 'approved', 'discount_approved': True})
        
    @api.multi
    def send_by_email(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        template = self.env.ref('target_features.proforma_email_template_mk', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.proforma.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
        
    @api.model
    def create(self, vals):
        res = super(account_proforma_invoice, self).create(vals)
        if res.second_approval and res.state == 'draft':
            res.update({'state': 'waiting_approval'})
        return res
        
    @api.multi
    def write(self, vals):
        res = super(account_proforma_invoice, self).write(vals)
        for order in self:
            if order.second_approval and order.state == 'draft':
                order.update({'state': 'waiting_approval'})
        return res
