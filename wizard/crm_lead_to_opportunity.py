# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class crm_lead2opportunity_partner(models.TransientModel):

    _inherit = 'crm.lead2opportunity.partner'

    def default_get(self, cr, uid, fields, context=None):
        """
        Default get for name, opportunity_ids.
        If there is an exisitng partner link to the lead, find all existing
        opportunities links with this partner to merge all information together
        """
        lead_obj = self.pool.get('crm.lead')

        res = super(crm_lead2opportunity_partner, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            tomerge = [int(context['active_id'])]

            partner_id = res.get('partner_id')
            lead = lead_obj.browse(cr, uid, int(context['active_id']), context=context)
            email = lead.partner_id and lead.partner_id.email or lead.email_from

            tomerge.extend(self._get_duplicated_leads(cr, uid, partner_id, email, include_lost=True, context=context))
            tomerge = list(set(tomerge))

            if 'action' in fields and not res.get('action'):
                res.update({'action': partner_id and 'exist' or 'create'})
            if 'partner_id' in fields:
                res.update({'partner_id': partner_id})
            if 'name' in fields:
                res.update({'name': 'convert'})
            if 'opportunity_ids' in fields and len(tomerge) >= 2:
                res.update({'opportunity_ids': tomerge})
            if lead.user_id:
                res.update({'user_id': lead.user_id.id})
            if lead.section_id:
                res.update({'section_id': lead.section_id.id})
        return res
    