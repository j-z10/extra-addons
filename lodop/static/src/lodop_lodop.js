odoo.define("lodop.lodop", function (require) {
    'use strict';

    var CreatedOKLodop7766 = null;
    var Class = require('web.Class');
    var ajax = require('web.ajax');
    var web_client = require('web.web_client');

    function do_warn(message) {
        return web_client.action_manager.do_warn('LODOP加载失败', message, true);
    }

//====判断是否需要安装CLodop云打印服务器:====
    function needCLodop() {
        try {
            var ua = navigator.userAgent;
            if (ua.match(/Windows\sPhone/i) !== null) return true;
            if (ua.match(/iPhone|iPod/i) !== null) return true;
            if (ua.match(/Android/i) !== null) return true;
            if (ua.match(/Edge\D?\d+/i) !== null) return true;

            var verTrident = ua.match(/Trident\D?\d+/i);
            var verIE = ua.match(/MSIE\D?\d+/i);
            var verOPR = ua.match(/OPR\D?\d+/i);
            var verFF = ua.match(/Firefox\D?\d+/i);
            var x64 = ua.match(/x64/i);
            if ((verTrident === null) && (verIE === null) && (x64 !== null)) {
                return true;
            } else if (verFF !== null) {
                verFF = verFF[0].match(/\d+/);
                if ((verFF[0] >= 41) || (x64 !== null)) return true;
            } else if (verOPR !== null) {
                verOPR = verOPR[0].match(/\d+/);
                if (verOPR[0] >= 32) return true;
            } else if ((verTrident === null) && (verIE === null)) {
                var verChrome = ua.match(/Chrome\D?\d+/i);
                if (verChrome !== null) {
                    verChrome = verChrome[0].match(/\d+/);
                    if (verChrome[0] >= 41) return true;
                }
            }
            return false;
        } catch (err) {
            return true;
        }
    }

//====页面引用CLodop云打印必须的JS文件：====
    function loadRequiredJS() {
        var url_1 = "http://localhost:8000/CLodopfuncs.js?priority=1";
        var url_2 = "http://localhost:18000/CLodopfuncs.js?priority=0";
        return $.when(ajax.loadJS(url_1), ajax.loadJS(url_2));
    }

//====获取LODOP对象的主过程：====
    function getLodop(oOBJECT, oEMBED) {
        var strHtmInstall = "<div style='color:red;font-size:14px;padding:4px 0;background-color:#d3d3d3'>打印控件未安装!点击这里<a href='http://www.lodop.net/download.html' target='_blank'>执行下载安装</a>,安装后请刷新页面或重新进入。</div>";
        var strHtmUpdate = "<div style='color:red;font-size:14px;padding:4px 0;background-color:#d3d3d3'>打印控件需要升级!点击这里<a href='http://www.lodop.net/download.html' target='_blank'>执行下载安装</a>,升级后请重新进入。</div>";
        var strHtm64_Install = "<div style='color:red;font-size:14px;padding:4px 0;background-color:#d3d3d3'>打印控件未安装!点击这里<a href='http://www.lodop.net/download.html' target='_blank'>执行下载安装</a>,安装后请刷新页面或重新进入。</div>";
        var strHtm64_Update = "<div style='color:red;font-size:14px;padding:4px 0;background-color:#d3d3d3'>打印控件需要升级!点击这里<a href='http://www.lodop.net/download.html' target='_blank'>执行下载安装</a>,升级后请重新进入。</div>";
        var strHtmFireFox = "<br><div style='color:red;font-size:14px;padding:4px 0;background-color:#d3d3d3'>（注意：如曾安装过Lodop旧版附件npActiveXPLugin,请在【工具】->【附加组件】->【扩展】中先卸它）</div>";
        var strHtmChrome = "<br><div style='color:red;font-size:14px;padding:4px 0;background-color:#d3d3d3'>(如果此前正常，仅因浏览器升级或重安装而出问题，需重新执行以上安装）</div>";
        var strCLodopInstall = "<div style='color:red;font-size:14px;padding:4px 0;background-color:#d3d3d3'>CLodop云打印服务(localhost本地)未安装启动!点击这里<a href='http://www.lodop.net/download.html' target='_blank'>执行下载安装</a>,安装后请刷新页面。</div>";
        var strCLodopUpdate = "<div style='color:red;font-size:14px;padding:4px 0;background-color:#d3d3d3'>CLodop云打印服务需升级!点击这里<a href='http://www.lodop.net/download.html' target='_blank'>执行下载安装</a>,升级后请刷新页面。</div>";
        var LODOP;
        try {
            var isIE = (navigator.userAgent.indexOf('MSIE') >= 0) || (navigator.userAgent.indexOf('Trident') >= 0);
            if (needCLodop()) {
                try {
                    LODOP = getCLodop();
                }
                catch (err) {
                }
                if (!LODOP && document.readyState !== "complete") {
                    alert("C-Lodop没准备好，请稍后再试！");
                    return;
                }
                if (!LODOP) {
                    do_warn(strCLodopInstall);
                    return;
                } else {
                    if (CLODOP.CVERSION < "3.0.2.8") {
                        do_warn(strCLodopUpdate);
                    }
                    if (oEMBED && oEMBED.parentNode) oEMBED.parentNode.removeChild(oEMBED);
                    if (oOBJECT && oOBJECT.parentNode) oOBJECT.parentNode.removeChild(oOBJECT);
                }
            } else {
                var is64IE = isIE && (navigator.userAgent.indexOf('x64') >= 0);
                //=====如果页面有Lodop就直接使用，没有则新建:==========
                if (oOBJECT !== undefined || oEMBED !== undefined) {
                    if (isIE) LODOP = oOBJECT; else LODOP = oEMBED;
                } else if (CreatedOKLodop7766 === null) {
                    LODOP = document.createElement("object");
                    LODOP.setAttribute("width", 0);
                    LODOP.setAttribute("height", 0);
                    LODOP.setAttribute("style", "position:absolute;left:0px;top:-100px;width:0px;height:0px;");
                    if (isIE) LODOP.setAttribute("classid", "clsid:2105C259-1E0C-4534-8141-A753534CB4CA");
                    else LODOP.setAttribute("type", "application/x-print-lodop");
                    document.documentElement.appendChild(LODOP);
                    CreatedOKLodop7766 = LODOP;
                } else LODOP = CreatedOKLodop7766;
                //=====Lodop插件未安装时提示下载地址:==========
                if ((LODOP === null) || (typeof(LODOP.VERSION) === "undefined")) {
                    if (navigator.userAgent.indexOf('Chrome') >= 0) {
                        do_warn(strHtmChrome);
                    } else if (navigator.userAgent.indexOf('Firefox') >= 0) {
                        do_warn(strHtmFireFox);
                    } else {
                        do_warn(strHtmInstall);
                    }
                    return LODOP;
                }
            }
            if (LODOP.VERSION < "6.2.2.0") {
                if (!needCLodop()) {
                    do_warn(strHtmUpdate);
                }
                return LODOP;
            }
            //===如下空白位置适合调用统一功能(如注册语句、语言选择等):===
            LODOP.SET_LICENSES("西域供应链（上海）有限公司", "CD8263A5A632F055701990DA499CEA172E8", "西域供應鏈（上海）有限公司", "65F5157311C52ECE9D397C13D20F65811AB");
            LODOP.SET_LICENSES("THIRD LICENSE", "", "Western Region Supply Chain (Shanghai) Co., Ltd.", "E09697CF1666B72C0F3A65B8D35D6D0A87F");
            //===========================================================
            return LODOP;
        } catch (err) {
            alert("getLodop出错:" + err);
        }
    }

    return {
        getLodop: getLodop,
        loadRequiredJS: loadRequiredJS
    };

});



