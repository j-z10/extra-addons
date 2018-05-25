odoo.define('form_no_edit.form_no_edit', function(require){
    var FormView = require('web.FormView');

    FormView.include({
        load_record: function(record){
            var self = this;
            return this._super(record).then(function(){
                if (self.options.action && self.options.action.target !== 'new' && self.options.action.context){
                    var no_edit = self.options.action.context.form_no_edit;
                    if (no_edit !== undefined) {
                        var res = self.compute_domain(no_edit);

                        if (res === true) {
                            if (self.get('actual_mode') !== 'view') {
                                self.$buttons.find('.o_form_button_cancel').trigger('click');
                            }
                            self.$buttons.find('.o_form_buttons_view').hide()
                        } else {
                            if (self.get('actual_mode') === 'view') {
                                self.$buttons.find('.o_form_buttons_view').show()
                            }
                        }
                    }
                }
            })
        }
    })
});