odoo.define('field_widget.basic_view', function(require){
'use strict';

var core = require('web.core');
var BasicView = require('web.BasicView');
var Sidebar = require('web.Sidebar');

var _t = core._t;

BasicView.include({
    init: function(viewInfo, params){
        this._super.apply(this, arguments);
        this.controllerParams.archiveEnabled = 'active' in viewInfo.fields;
        if ('active' in viewInfo.fields) {
            if (viewInfo.arch.attrs.archive) {
                this.controllerParams.archiveEnabled = JSON.parse(viewInfo.arch.attrs.archive);
            } else {
                this.controllerParams.archiveEnabled = true;
            }
        } else {
            this.controllerParams.archiveEnabled = false;
        }
    }
});

Sidebar.include({
    _addItems: function (sectionCode, items) {
        var controller = this.getParent();
        var view_manager = controller.getParent();
        var arch = view_manager.active_view.fields_view.arch;
        var exportable = arch.attrs.export ? JSON.parse(arch.attrs.export) : true;
        if (!exportable) {
            items = items.filter(function(v){
                return v.label !== _t("Export");
            });
        }
        return this._super.call(this, sectionCode, items);
    }
})
});