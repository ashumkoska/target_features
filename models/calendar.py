# -*- coding: utf-8 -*-

from openerp import api, models, fields, _
from openerp import tools


class calendar_attendee(models.Model):
    
    _inherit = 'calendar.attendee'
    
    def _send_mail_to_attendees(self, cr, uid, ids, email_from=tools.config.get('email_from', False),
                                template_xmlid='calendar_template_meeting_invitation_mk', force=False, context=None):
        '''
        Send mail for event invitation to event attendees.
        @param email_from: email address for user sending the mail
        @param force: If set to True, email will be sent to user himself. Usefull for example for alert, ...
        '''
        res = False

        if self.pool['ir.config_parameter'].get_param(cr, uid, 'calendar.block_mail', default=False) or context.get('no_mail_to_attendees'):
            return res

        mail_ids = []
        data_pool = self.pool['ir.model.data']
        mailmess_pool = self.pool['mail.message']
        mail_pool = self.pool['mail.mail']
        template_pool = self.pool['email.template']
        local_context = context.copy()
        color = {
            'needsAction': 'grey',
            'accepted': 'green',
            'tentative': '#FFFF00',
            'declined': 'red'
        }

        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        if template_xmlid == 'calendar_template_meeting_invitation_mk':
            dummy, template_id = data_pool.get_object_reference(cr, uid, 'target_features', template_xmlid)
        else:
            dummy, template_id = data_pool.get_object_reference(cr, uid, 'calendar', template_xmlid)
        dummy, act_id = data_pool.get_object_reference(cr, uid, 'calendar', 'view_calendar_event_calendar')
        local_context.update({
            'color': color,
            'action_id': self.pool['ir.actions.act_window'].search(cr, uid, [('view_id', '=', act_id)], context=context)[0],
            'dbname': cr.dbname,
            'base_url': self.pool['ir.config_parameter'].get_param(cr, uid, 'web.base.url', default='http://localhost:8069', context=context)
        })

        for attendee in self.browse(cr, uid, ids, context=context):
            if attendee.email and email_from and (attendee.email != email_from or force):
                ics_file = self.get_ics_file(cr, uid, attendee.event_id, context=context)
                mail_id = template_pool.send_mail(cr, uid, template_id, attendee.id, context=local_context)

                vals = {}
                if ics_file:
                    vals['attachment_ids'] = [(0, 0, {'name': 'invitation.ics',
                                                      'datas_fname': 'invitation.ics',
                                                      'datas': str(ics_file).encode('base64')})]
                vals['model'] = None  # We don't want to have the mail in the tchatter while in queue!
                vals['res_id'] = False
                the_mailmess = mail_pool.browse(cr, uid, mail_id, context=context).mail_message_id
                mailmess_pool.write(cr, uid, [the_mailmess.id], vals, context=context)
                mail_ids.append(mail_id)

        if mail_ids:
            res = mail_pool.send(cr, uid, mail_ids, context=context)

        return res
