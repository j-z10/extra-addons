odoo.define('workflow.view_manager', function(require){
'use strict';

var Context = require('web.Context');
var session = require('web.session');
var ViewManager = require('web.ViewManager');

ViewManager.include({
    do_execute_action: function (action_data, env, on_closed) {
        if (action_data.type === 'workflow') {
            return this.do_execute_workflow_action(action_data, env, on_closed);
        } else {
            return this._super.apply(this, arguments);
        }
    },
    do_execute_workflow_action: function(action_data, env, on_closed) {
        var self = this;
        var result_handler = on_closed || function () {};
        var recordID = env.currentID || null;
        // just copy code from /web/static/.../chrome/view_manager.js
        var handler = function (action) {
            var effect = false;
            if (action_data.effect) {
                effect = pyeval.py_eval(action_data.effect);
            }

            if (action && action.constructor === Object) {
                var ncontext = new Context(
                    _.object(_.reject(_.pairs(self.env.context), function(pair) {
                      return pair[0].match('^(?:(?:default_|search_default_|show_).+|.+_view_ref|group_by|group_by_no_leaf|active_id|active_ids)$') !== null;
                    }))
                );
                ncontext.add(action_data.context || {});
                ncontext.add({active_model: env.model});
                if (recordID) {
                    ncontext.add({
                        active_id: recordID,
                        active_ids: [recordID]
                    });
                }
                ncontext.add(action.context || {});
                action.context = ncontext;
                action.effect = effect || action.effect;
                return self.do_action(action, {
                    on_close: result_handler
                });
            } else {
                self.do_action({"type":"ir.actions.act_window_close", 'effect': effect});
                return result_handler();
            }
        };

        return session.rpc('/workflow/exec_workflow', {
            model: env.model,
            id: recordID,
            signal: action_data.name
        }).then(handler)
    }
});
});