odoo.define('form_no_edit.form_no_edit', function(require){
    var FormController = require('web.FormController');
    var Domain = require('web.Domain');


    FormController.include({
        decideToShowButtons: function(){
            var record = this.model.get(this.handle),
                actionCtx = record.getContext(),
                evalContext = record.evalContext;
            if (actionCtx.form_no_edit){
                var d = new Domain(actionCtx.form_no_edit).compute(evalContext);
                if (d === true) {
                    if (this.mode === 'edit') {
                        // 本条可编辑，进入编辑状态后，通过pager切换时，取消编辑状态
                        this.$buttons.find('.o_form_button_cancel').trigger('click');
                    }
                    this.$buttons.find('.o_form_button_edit').hide()
                } else {
                    if (this.mode === 'readonly') {
                        this.$buttons.find('.o_form_button_edit').show()
                    }
                }
            }
        },
        renderButtons: function(){
            // 从别的menu item访问到这边, 并且进入到form view
            // console.log('render buttons');
            this._super.apply(this, arguments);
            this.decideToShowButtons();
        },
        reload: function(){
            // form view 下，通过pager切换上一条，下一条时
            var self = this;
            // console.log('reload record');
            return this._super.apply(this, arguments).then(function(res){
                self.decideToShowButtons();
                return res;
            });
        },
        saveRecord: function() {
            // 主要是为了创建record的时候；编辑record的话，这里会调用一次decideToShowButtons, reload那里也会调用一次
            // console.log('save record');
            var self = this;
            return this._super.apply(this, arguments).then(function(res){
                self.decideToShowButtons();
                return res;
            })
        }
    })
});
