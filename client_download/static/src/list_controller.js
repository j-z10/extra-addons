odoo.define('client_download.download', function(require){
'use strict';

var ListController = require('web.ListController');
var field_utils = require('web.field_utils');

ListController.include({
    init: function(parent, model, renderer, params){
        this._super.apply(this, arguments);
        this.client_download_type = params.initialState.context.client_download_type;
    },
    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        if (!this.noLeaf && this.hasButtons) {
            this.$buttons.on('click', '.o_list_button_download', this._onButtonDownload.bind(this));
        }
    },
    _getPageData: function(){
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
        data.push(headers.map(function(n){return self.renderer.state.fields[n].string}));
        data.push.apply(data, rows);
        return data;
    },
    _onButtonDownload: function() {
        if (this.client_download_type === 'csv') {
            return this.exportToCsv(this.modelName + '.csv', this._getPageData());
        } else {
            return this.exportToExcel(this.modelName + '.xls');
        }
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

        return this.exportDownload(filename, csvFile, {type: 'text/csv;charset=utf-8;'});
    },
    exportToExcel: function (filename) {
        var tab_text = "";
        var tab = this.$el.find('table')[0];
        if (!tab) {
            return;
        }
        if (tab.tHead) {
            tab_text += '<tr bgcolor=\'#87AFC6\'>' + tab.rows[0].innerHTML+"</tr>";
        }
        for(var j=1; j < tab.rows.length ; j++) {
            tab_text += '<tr>' + tab.rows[j].innerHTML+"</tr>";
        }
        tab_text= tab_text.replace(/<A[^>]*>|<\/A>/g, "");//remove if u want links in your table
        tab_text= tab_text.replace(/<img[^>]*>/gi,""); // remove if u want images in your table
        tab_text= tab_text.replace(/<input[^>]*>|<\/input>/gi, ""); // reomves input params

        var
            template = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40"><meta http-equiv="content-type" content="application/vnd.ms-excel; charset=UTF-8"><head><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>{worksheet}</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--></head><body><table border="2px">{table}</table></body></html>',
            format = function (s, c) {
                return s.replace(/{(\w+)}/g, function (m, p) {
                    return c[p];
                })
            };
        var ctx = {
            worksheet: "Sheet 1" || 'Worksheet',
            table: tab_text
        };
        return this.exportDownload(filename, format(template, ctx), {type: 'application/vnd.ms-excel'});
    },
    exportDownload: function(filename, data, option){
        var blob = new Blob([data], option);
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