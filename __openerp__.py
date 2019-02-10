# -*- coding: utf-8 -*-

{
    'name': 'Target Features',
    'version': '8.0.1.0.0',
    'author': 'Neodata',
    'website': 'http://www.neodata.com.mk/en_US/',
    'support': 'contact@neodata.com.mk',
    'category': 'Extra Features',
    'summary': 'Additional Features for Target',
    'description': 'Additional Features for Target',
    'depends': [
        'purchase',
        'Target_Neodata',
        'marketing_crm',
        'base_user_role'
    ],
    'data': [        
        'security/target_roles.xml',
        'security/ir.model.access.csv',
        'security/target_rules.xml',
        'data/target_data.xml',
        'wizard/user_type_wiz.xml',
        'wizard/import_partners_leads_wiz.xml',
        'views/partner_note_views.xml',
        'views/target_views.xml',
        'views/activation_templates.xml',
        'views/expiration_templates.xml'
    ],
    'installable': True,
    'auto_install': True
}
