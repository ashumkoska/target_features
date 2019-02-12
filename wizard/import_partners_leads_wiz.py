# -*- coding: utf-8 -*-
import csv
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from openerp import api, models, fields, _
from openerp.exceptions import ValidationError, Warning


class import_partners_wiz(models.TransientModel):

    _name = 'import.partners.leads.wiz'
    _description = 'Import Leads Wizard'
    
    leads_file = fields.Binary(string='File')
    leads_filename = fields.Char(string='Filename')
    
    @api.multi
    def import_partners_leads(self):
        self.ensure_one()
        new_lead_ids = []
        if not any(self.leads_filename.endswith(ext) for ext in ['csv']):
            raise ValidationError(_('Please upload a valid CSV file.'))
        
        csv_content = self.leads_file.decode('base64')
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:
            # csv columns: 
            # SubjectID, Subject, CustomerName, Street, City, Zip, Country, 
            # Email, Phone, Mobile, TaxNumber, RegNumber, source, SalesPerson
            try:
                reg_number = str(row.get('RegNumber')) if row.get('RegNumber') else ''
                country_name = row.get('Country', '')
                source_name = row.get('source', '')
                user_name = row.get('SalesPerson', '')
                country = False
                if country_name:
                    country = self.env['res.country'].search(['|', ('code', '=', country_name), 
                                                              ('name', '=', country_name)], limit=1)
                source = False
                if source_name:
                    source = self.env['crm.tracking.source'].search([('name', '=', source_name)], limit=1)                
                user = False
                if user_name:
                    user = self.env['res.users'].search([('name', '=', user_name)], limit=1)
                # partner values
                partner_vals = {
                    'SubjectID': str(row.get('SubjectID')) if row.get('SubjectID') else '',
                    'name': row.get('CustomerName'),
                    'street': row.get('Street'),
                    'city': row.get('City'),
                    'zip': str(row.get('Zip')) if row.get('Zip') else '',
                    'country_id': country.id if country else False,
                    'email': row.get('Email'),
                    'phone': str(row.get('Phone')) if row.get('Phone') else '',
                    'mobile': str(row.get('Mobile')) if row.get('Mobile') else '',
                    'TaxNumber': row.get('TaxNumber'),
                }
            except Exception as e:
                raise Warning(_('The following error has occurred while reading the file: \n%s' % e))
            partner = self.env['res.partner'].search([('RegNumber', '=', reg_number)])
            # update values if partner exists
            if partner:
                partner.write(partner_vals)
            else:
                # create new partner
                partner_vals.update({'RegNumber': reg_number})
                partner = self.env['res.partner'].create(partner_vals)
            try:
                # lead values
                lead_vals = {
                    'name': row.get('Subject'),
                    'partner_name': row.get('CustomerName'),
                    'partner_id': partner.id,
                    'street': row.get('Street'),
                    'city': row.get('City'),
                    'zip': str(row.get('Zip')) if row.get('Zip') else '',
                    'country_id': country.id if country else False,
                    'email_from': row.get('Email'),
                    'phone': str(row.get('Phone')) if row.get('Phone') else '',
                    'mobile': str(row.get('Mobile')) if row.get('Mobile') else '',
                    'source_id': source.id if source else False,
                    'user_id': user.id if user else False
                }
            except Exception as e:
                raise Warning(_('The following error has occurred while reading the file: \n%s' % e))
            # create new lead
            lead = self.env['crm.lead'].create(lead_vals)
            new_lead_ids.append(lead.id)

        return {            
            'name': _('New Leads'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm.lead',
            'target': 'current',
            'domain': [('id', 'in', new_lead_ids)]
        }
