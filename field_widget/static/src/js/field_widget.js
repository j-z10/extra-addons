odoo.define('field_widget.widget', function(require){
'use strict';

var registry = require('web.field_registry');
var FieldFloat = registry.get('float');
var FieldChar = registry.get('char');

var FieldPercent = FieldFloat.extend({
    className: 'o_field_percent o_field_number',
    _formatValue: function(value) {
        if (this.mode === 'edit') {
            return this._super.apply(this, arguments);
        } else {
            return (value * 100).toFixed(2).replace(/\.?0+$/, '') + '%';
        }
    }
});

var FieldLimitedChar = FieldChar.extend({
    _renderReadonly: function () {
        var origin_val = this._formatValue(this.value),
            limit = this.attrs.options && this.attrs.options.limit || 0;
        if (limit && (origin_val.length > limit)) {
            var limited_val = origin_val.slice(0, limit);
            var html = '<span title="' + origin_val + '">' + limited_val + '...</span>';
            return this.$el.append($(html));
        } else {
            return this._super.apply(this, arguments);
        }
    },
});

registry.add('percent', FieldPercent);
registry.add('list.limited_char', FieldLimitedChar);
});