odoo.define('ajax_demo.demo', function (require) {
    var session = require('web.session');

    session.rpc('/web/dataset/call', {
        method: 'read',
        model: 'res.partner',
        args: [[1, 2, 3], ['name']]
    }).then(function(r){
        console.log(r);
    });

});