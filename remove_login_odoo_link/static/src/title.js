odoo.define('remove_login_odoo_link.title', function(require){
'use strict';

var AbstractWebClient = require('web.AbstractWebClient');

AbstractWebClient.include({
    init: function(){
        this._super.apply(this, arguments);
        this.set('title_part', {"zopenerp": window.odoo.session_info.main_company_name});
    },
    _title_changed: function(){
        if (this.get('title_part').zopenerp.indexOf('Odoo') > -1) return;
        return this._super.apply(this, arguments);
    }
})
});