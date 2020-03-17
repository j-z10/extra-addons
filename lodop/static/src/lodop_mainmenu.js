odoo.define('lodop_print.MainMenu', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var session = require('web.session');
    var lodop = require('lodop.lodop');

    function short_string(foo, num) {
        return (foo ? foo.slice(0, num) : '') + ((foo && foo.slice(num)) ? '...' : '');
    }

    var MainMenu = Widget.extend({
        template: 'lodop_print',
        init: function (parent, action) {
            this._super(parent);
            this.LODOP = null;
            this.context = action.context;
            this.e_map = {
                'special': this.special_lodop_print.bind(this)  // 后续就可以在e_map里面新增各种js的lodop打印
            };
        },
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return lodop.loadRequiredJS().always(function () {
                    // 如果loadjs成功，初始化LODOP
                    // 失败，getLodop将会提供下载链接
                    window.LODOP = self.LODOP = lodop.getLodop();
                }).then(function () {
                    if (self.LODOP.webskt && self.LODOP.webskt.readyState===1){
                        self.start_print();
                    } else {
                        window.On_CLodop_Opened=function(){
                            // 避免 websocket 没有准备好
                            self.start_print();
                            window.On_CLodop_Opened=null;
                        };
                    }
                });
            });
        },
        start_print: function () {
            var self = this;
            if (!self.LODOP) return;
            var length = self.context['rend_data_list'].length,
                $doing = self.$('.doing'),
                $percent = self.$('.percent'),
                $p_bar = self.$('.progress-bar'),
                $done = self.$('.done_doc'),
                i = 0;
            (function loop() {
                var cnt = i+1;
                var extra = cnt.toString() + " / " + length.toString();
                $doing.text("正在打印：" + extra);
                var val = self.context['rend_data_list'][i];
                if (self.e_map[val.options.type]){
                    self.e_map[val.options.type](val['rend_data'], val['options']);
                } else {
                    self.do_print(val['rend_data'], val['options'])
                }
                var percent = cnt / length * 100;
                $percent.text(extra);
                $p_bar.css({'width': percent + '%'});
                $done.text("已经完成：" + extra);
                i++;
                if (i < length) {
                    setTimeout(loop, length < 10 ? 100 : (length < 50 ? 50 : 20)); // 这样才能看到打印进度条的变动
                } else {
                    $doing.text("打印结束：" + extra);
                    setTimeout(function(){
                        $('button.close').click();
                    }, 500);
                }
            })();
        },
        do_print: function (rend_data, options) {
            var LODOP = this.LODOP;
            LODOP.PRINT_INIT(options.print_init_name || "页面打印");   //首先一个初始化语句
            LODOP.SET_PRINTER_INDEX(options.printer);
            if (options.pagesize.width !== -1 && options.pagesize.height !== -1) {
                LODOP.SET_PRINT_PAGESIZE(1, options.pagesize.width, options.pagesize.height, "自定义面单");
            }
            if (options.print_page_footer) {
                LODOP.ADD_PRINT_TABLE(0,0,"100%","80%",rend_data);
                // 打印页脚
                LODOP.SET_PRINT_STYLE("ItemType", 1);
                LODOP.SET_PRINT_STYLE("FontSize", 9);
                LODOP.ADD_PRINT_LINE("97%", 0, "97%", "100%", 0, 2);
                LODOP.ADD_PRINT_TEXT("98%", '60%', "25%", "20mm", '打印时间：' + LODOP.FORMAT("TIME:yyyy-mm-dd hh:mm:ss","now"));
                LODOP.SET_PRINT_STYLE("ItemType", 2);
                LODOP.ADD_PRINT_TEXT("98%", '85%', "14%", "20mm", '第#页/共&页');
                LODOP.SET_PRINT_STYLEA(0,"Alignment",3);
            } else {
                LODOP.ADD_PRINT_HTM(0,0,"100%","100%",rend_data);
            }
            LODOP.PRINT();
        },
        special_lodop_print: function (rend_data, options) {
            var LODOP = this.LODOP;
            LODOP.PRINT_INIT(options.print_init_name || "面单打印");   //首先一个初始化语句
            LODOP.SET_PRINTER_INDEX(options.printer);
            LODOP.SET_PRINT_PAGESIZE(1, options.pagesize.width, options.pagesize.height, "SKU标签打印");
            // do something LODOP js setting
            LODOP.PRINT();
        }
    });

    core.action_registry.add('lodop_print_main_menu', MainMenu);

    return {
        MainMenu: MainMenu
    };

});
