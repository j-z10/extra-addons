odoo.define('base_export_without_external_id.export', function(require){
'use strict';

var Dialog = require('web.Dialog');
var framework = require('web.framework');
var DataExport = require('web.DataExport');
var pyeval = require('web.pyeval');
var crash_manager = require('web.crash_manager');
var core = require('web.core');
var _t = core._t;

DataExport.include({
    export_data: function() {
        var self = this;
        var exported_fields = this.$('.o_fields_list option').map(function () {
            return {
                name: (self.records[this.value] || this).value,
                label: this.textContent || this.innerText // DOM property is textContent, but IE8 only knows innerText
            };
        }).get();

        if (_.isEmpty(exported_fields)) {
            Dialog.alert(this, _t("Please select fields to export..."));
            return;
        }
        if (!this.$('.o_export_with_out_external_id')[0].checked){
            exported_fields.unshift({name: 'id', label: 'External ID'});
        }

        var export_format = this.$export_format_inputs.filter(':checked').val();

        framework.blockUI();
        this.getSession().get_file({
            url: '/web/export/' + export_format,
            data: {data: JSON.stringify({
                model: this.record.model,
                fields: exported_fields,
                ids: this.ids_to_export,
                domain: this.domain,
                context: pyeval.eval('contexts', [this.record.getContext()]),
                import_compat: !!this.$import_compat_radios.filter(':checked').val(),
            })},
            complete: framework.unblockUI,
            error: crash_manager.rpc_error.bind(crash_manager),
        });
    }
});
});