// [[
//    @brief    host 与 web ui 的通信接口
//    @author   yilungao
//    @version  1.0
//    @date     2017-11-07
// ]]


// -- on_hostapp_callback: tcls 通知到 js 的消息接口
// @ callback_name: 消息组名称，详见 common_define.js中的定义
// @ json_param: 消息内容，格式如下,
// {
// "head": 
// {
//   "cmd":cmd_id // 定义在 common_define.js 中，与 flash 版本完全一致
// },
// "body": 
// {
//   "key1":value1
//   "key2":value2
//   ...
// }
// }
function on_hostapp_callback(callback_name, json_param) {
    var param = jQuery.parseJSON(json_param);

    if (param == null || param == undefined) return;


    if (tcls_callback.on_tcls_notify == callback_name) {
        // alert("OncallBack......" + callback_name + "  Param : " + json_param);
        cmd_id = param.head.cmd;
        switch (cmd_id) {
            case tcls_sc_cmd_id.SC_INITSUCCESS: {
                // tcls_init_success(param.body);
                break;
            };
            default:
                break;
        }
    };
}

// -- send_msg_to_host: js 通知到 tcls 的消息接口
// @ interface_name: 消息组名称, 详见 common_define.js中的定义
// @ json_param: 消息内容，格式如下,
// {
// "head": 
// {
//   "cmd":cmd_id // 定义在 common_define.js 中，与 flash 版本完全一致
// },
// "body": 
// {
//   "key1":value1
//   "key2":value2
//   ...
// }
// }
function send_msg_to_host(interface_name, json_data) {
    // alert("send_msg_to_host..." + interface_name + ".." + json_data);
    window.external.callcpp(interface_name, json_data);
}