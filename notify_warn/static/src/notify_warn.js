odoo.define('notify_warn', function(require){
'use strict';

var web_client = require('web.web_client');
var core = require('web.core');

function NotifyWarn(parent, action) {
    console.log(action);
    var params = action.params || {};
    if (params.warn) {
        web_client.do_warn(params.warn.title, params.warn.message, params.warn.sticky || undefined);
    } else if (params.notify) {
        web_client.do_notify(params.warn.title, params.warn.message, params.warn.sticky || undefined);
    }
}
core.action_registry.add('notify_warn', NotifyWarn);

return NotifyWarn;
});