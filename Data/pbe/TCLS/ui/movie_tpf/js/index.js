$(document).ready(function() {
    mediaController = MediaController.create();
    mediaController.initialize();

    serverController = ServerController.create();
    serverController.initialize();
    serverController.hide(null, 0);

    sendHostMessage(100000);
    // enterServer();
});

var mediaController = null;
var serverController = null;
var current_host_state = 0;

function sendHostMessage(cmd) {
    var tdr_var = {
        head: {
            cmd: cmd
        },
        body: {
            plugin_updated: true
        }
    };
    var str_param = JSON.stringify(tdr_var);
    window.external.callcpp("UI_INIT_COMPLETE", str_param);
}

function on_hostapp_callback(callback_name, json_param) {
    // alert("OncallBack......" + callback_name + "  Param : " + json_param);
    var param = jQuery.parseJSON(json_param);

    if (param == null || param == undefined) return;

    switch (callback_name) {
        case "notify_host_state":
            switch (param.state) {
                case 2:
                    if (current_host_state != 2) {
                        enterLogin();
                        current_host_state = 2;
                    }
                    break;
                case 3:
                    if (current_host_state != 3) {
                        enterServer();
                        current_host_state = 3;
                    }
                    break;
            }
            // alert("host state change:" + param.state);
            break;
        case "notify_music_option":
            switch (param.music_option) {
                case 0:
                    mediaController.setMute(true);
                    serverController.setMute(true);
                    break;
                case 1:
                    mediaController.setMute(false);
                    serverController.setMute(false);
                    break;
            }
            break;
        case "notify_select_server":
            if (serverController) {
                serverController.selectServer(param);
            }
            // alert("select server:" + param.server_id);
            break;
        case "notify_enter_server":
            // alert("enter server:" + param.server_id);
            break;
        default:
            break;
    }
}

function enterUpdate() {
    mediaController.enter(1);
    serverController.hide();
}

function enterLogin() {
    mediaController.enter(2);
    serverController.hide();
}

function enterServer() {
    mediaController.enter(3);
    serverController.show();

    // serverController.selectServer({server_id:4097});
}