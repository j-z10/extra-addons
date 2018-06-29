odoo.define('client_download.download', function(require){
'use strict';

var ListController = require('web.ListController');
var field_utils = require('web.field_utils');

ListController.include({
    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        if (!this.noLeaf && this.hasButtons) {
            this.$buttons.on('click', '.o_list_button_download', this._onButtonDownload.bind(this));
        }
    },
    _onButtonDownload: function() {
        console.log('self is', this);
        var self = this;
        var headers = this.renderer.columns.map(function(v){return v.attrs.name});
        var rows = this.renderer.state.data.map(function(record){
            return headers.map(function(name){
                var field = self.renderer.state.fields[name];
                var value = record.data[name];
                return field_utils.format[field.type](value, field, {
                    data: record.data,
                    escape: true
                });
            });
        });
        var data = [];
        data.push(headers);
        data.push.apply(data, rows);
        this.exportToCsv(this.modelName + '.csv', data);

    },
    exportToCsv: function (filename, rows) {
        var processRow = function (row) {
            var finalVal = '';
            for (var j = 0; j < row.length; j++) {
                var innerValue = row[j] === null ? '' : row[j].toString();
                if (row[j] instanceof Date) {
                    innerValue = row[j].toLocaleString();
                }
                var result = innerValue.replace(/"/g, '""');
                if (result.search(/("|,|\n)/g) >= 0)
                    result = '"' + result + '"';
                if (j > 0)
                    finalVal += ',';
                finalVal += result;
            }
            return finalVal + '\n';
        };

        // 如果是windows, 使用带BOM的csv文件，用来解决乱码的问题
        var csvFile = navigator.platform.toUpperCase().indexOf('WIN') > -1 ? '\ufeff' : '';
        for (var i = 0; i < rows.length; i++) {
            csvFile += processRow(rows[i]);
        }

        var blob = new Blob([csvFile], {type: 'text/csv;charset=utf-8;'});
        if (navigator.msSaveBlob) { // IE 10+
            navigator.msSaveBlob(blob, filename);
        } else {
            var link = document.createElement("a");
            if (link.download !== undefined) { // feature detection
                // Browsers that support HTML5 download attribute
                var url = URL.createObjectURL(blob);
                link.setAttribute("href", url);
                link.setAttribute("download", filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        }
    }
});

});