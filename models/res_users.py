# -*- coding: utf-8 -*-

from openerp import api, models, fields, _


class res_users(models.Model):
    
    _inherit = 'res.users'
    
    @api.multi
    def reset_signature(self):
        self.ensure_one()
        default_signature = '''
            <p class="text-muted">
                <br/><br/>
                <b style="color: red;">ТАРГЕТ ГРУП ДОО Скопје</b><br>
                <span>Ул. Кеј Димитар Влахов бр. 3-1/1/3</span><br>
                <span>1000 Скопје, Р. Македонија</span><br>
                <span>Тел/Факс: +389 (2) 3117 100</span><br>
                <span>Е-маил: </span><a href="mailto:info@targetgroup.mk">info@targetgroup.mk</a><br>
                <a href="http://targetgroup.mk/">www.targetgroup.mk</a>
            </p>
            <p>
                <b style="color: red;"><i>За паметни деловни одлуки!</i></b><br>
                <a href="http://targetgroup.mk/">
                  <img src="http://targetgroup.mk/wp-content/uploads/2019/03/logo.jpg" style="max-width: 156px;">
                  <img src="https://www.biznismreza.mk/themes/biznis-mreza/assets/img/BM_Logo.png" style="max-width: 156px; padding-left: 10px; padding-bottom: 5px;">
                </a>
            </p>
        '''
        self.signature = default_signature
        view_id = self.env.ref('base.view_users_form_simple_modif').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',            
            'view_id': view_id,
            'target': 'new',
            'context': self.env.context
        }
        