# -*- coding: utf-8 -*-

from xlrd import open_workbook
from xlrd.sheet import ctype_text
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
        if not any(self.leads_filename.endswith(ext) for ext in ['xls', 'xlsx']):
            raise ValidationError(_('Please upload a valid Excel file.'))
        file_data = self.leads_file.decode('base64')
        wb = open_workbook(file_contents=file_data)
        leads_sheet = wb.sheet_by_index(0)
        columns = {leads_sheet.cell(0, col_index).value: col_index for col_index in xrange(leads_sheet.ncols)}
        for row_i in range(2, leads_sheet.nrows):
            # xlsx columns: 
            # SubjectID, Subject, CustomerName, Street, City, Zip, Country, 
            # Email, Phone, Mobile, TaxNumber, RegNumber, source, SalesPerson
            try:
                reg_number = str(int(leads_sheet.cell(row_i, columns['RegNumber']).value))
                country_name = leads_sheet.cell(row_i, columns['Country']).value
                source_name = leads_sheet.cell(row_i, columns['source']).value
                user_name = leads_sheet.cell(row_i, columns['SalesPerson']).value
                country = self.env['res.country'].search(['|', ('code', '=', country_name), 
                                                          ('name', '=', country_name)], limit=1)
                source = self.env['crm.tracking.source'].search([('name', '=', source_name)], limit=1)
                user = self.env['res.users'].search([('name', '=', user_name)], limit=1)
                # partner values
                partner_vals = {
                    'SubjectID': str(int(leads_sheet.cell(row_i, columns['SubjectID']).value)),
                    'name': leads_sheet.cell(row_i, columns['CustomerName']).value,
                    'street': leads_sheet.cell(row_i, columns['Street']).value,
                    'city': leads_sheet.cell(row_i, columns['City']).value,
                    'zip': str(int(leads_sheet.cell(row_i, columns['Zip']).value)),
                    'country_id': country.id if country else False,
                    'email': leads_sheet.cell(row_i, columns['Email']).value,
                    'phone': str(int(leads_sheet.cell(row_i, columns['Phone']).value)),
                    'mobile': str(int(leads_sheet.cell(row_i, columns['Mobile']).value)),
                    'TaxNumber': leads_sheet.cell(row_i, columns['TaxNumber']).value
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
                    'name': leads_sheet.cell(row_i, columns['Subject']).value,
                    'partner_name': leads_sheet.cell(row_i, columns['CustomerName']).value,
                    'partner_id': partner.id,
                    'street': leads_sheet.cell(row_i, columns['Street']).value,
                    'city': leads_sheet.cell(row_i, columns['City']).value,
                    'zip': str(int(leads_sheet.cell(row_i, columns['Zip']).value)),
                    'country_id': country.id if country else False,
                    'email_from': leads_sheet.cell(row_i, columns['Email']).value,
                    'phone': str(int(leads_sheet.cell(row_i, columns['Phone']).value)),
                    'mobile': str(int(leads_sheet.cell(row_i, columns['Mobile']).value)),
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
