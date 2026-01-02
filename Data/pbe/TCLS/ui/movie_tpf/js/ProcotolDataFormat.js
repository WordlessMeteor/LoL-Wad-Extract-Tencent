{
    "head": {
        "cmd": cmd_id,
    },
    "body": {}
}


{
    "head": {
        "cmd": SC_TASFINDVITUS,
    },
    "body": {
        "tas_scan_proc": 100
    }
}



// init success
{
    "head": {
        "cmd": SC_INITSUCCESS,
    },
    "body": {
        "force_update_first": 0,
        "enable_64_bit": 0,
        "use_64_bit": 0,
        "close_sound": 0,
        "close_tgp": 0,
        "full_screen": 0,
        "set_default_pixels": 0,
        "last_uin": "295378891",
        "enable_wechat_login": 0, // 是否支持微信登录
        "read_license": 1,
        "enable_wechat_gray_publish": 1,
        "wechat_bind_not_ask": 1
    }
},

// 测速数据
{
    "head": {
        "cmd": SC_GETNETSPEEDSUCCESS,
    },
    "body": {
        "arg_first": 1033,
        "arg_second": 100
    }
}

{
    "head": {
        "cmd": SC_GETNETSPEEDFAIL,
    },
    "body": {
        "arg_first": 1033,
        "arg_second": 100
    }
}


// 微信登录接口
/*
1. 是否激活微信登录？ client 2 web
	cmd : SC_INITSUCCESS
	data : enable_wechat_login

2. 获取二维码..  web 2 client
	cmd : CS_GETWECHATQRCODE

3. 二维码已准备.. client 2 web
	cmd : SC_WECHAT_QR_READY
	data : pic_path

4. 通知微信登录结果.. client 2 web
	success
		cmd : SC_WECHAT_LOGIN_SUCCESS
	failed
		cmd : SC_WECHAT_QR_READY
*/
{
    // 请求微信二维码，返回二维码地址
    {
        "head": {
            "cmd": CS_GETWECHATQRCODE,
        },
        "body": {}
    },

    // 登录失败，ui 显示error_code即可
    {
        "head": {
            "cmd": SC_WECHAT_LOGIN_FAIL,
        },
        "body": {
            "error_code": 0, // 7000000:未实名帐号
            "error_type": 0
        }
    },

    // 登录成功
    {
        "head": {
            "cmd": SC_WECHAT_LOGIN_SUCCESS,
        },
        "body": {}
    },


    //  资源路径：TCLS/ui/res/wechat.bmp
    {
        "head": {
            "cmd": SC_WECHAT_QR_READY,
        },
        "body": {
            "pic_path": "wechat.bmp"
        }
    }
},


// Login DATA host to web
{
    {
        "head": {
            "cmd": SC_SHOWLOADING,
        },
        "body": {
            "data": 0
        }
    },

    {
        "head": {
            "cmd": SC_QRLOGIN,
        },
        "body": {
            "pic_path": "...",
            "tips_id": 1,
            "logo_id": 2
        }
    },

    {
        "head": {
            "cmd": SC_INPUTERROR,
        },
        "body": {
            "error_id": error_id
        }
    },

    {
        "head": {
            "cmd": SC_LOGINFAIL,
        },
        "body": {
            "arg_first": "..."
        }
    },

    {
        "head": {
            "cmd": SC_LOGINSCUCCESS,
        },
        "body": {
            "arg_first": "..."
            "arg_first": 1
        }
    },

    {
        "head": {
            "cmd": SC_LOGIN_JUMPTONEXT,
        },
        "body": {}
    },

    {
        "head": {
            "cmd": SC_REGISTERIDENTITY,
        },
        "body": {}
    },

    {
        "head": {
            "cmd": SC_GETHISTORYACCOUNT,
        },
        "body": {
            "history_count": count,
            "history_list": [
                "295378891",
                "295378892",
                "295378893",
                ...
            ],
            "last_uin": "29578891",
            "full_screen": 1,
            "read_lisence": 1,
            "record_uin": 1,
            "screen_index": 1,
            "close_tgp": 1,
            "open_tas": 1,
            "close_sound": 1
        }
    },

    {
        "head": {
            "cmd": SC_BEGINQUICKLOGINQQ,
        },
        "body": {
            "qq_info": [{
                "uin": "295378891",
                "nick_name": "gaoyilun's qq"
            }]
        }
    },

    {
        "head": {
            "cmd": SC_LOGIN_NOTIFYMESSAGEBOX,
        },
        "body": {
            "cmd": 0
        }
    },

    {
        "head": {
            "cmd": SC_TASPROCESS,
        },
        "body": {
            "tas_scan_proc": 95
        }
    },

    {
        "head": {
            "cmd": SC_ENTER,
        },
        "body": {}
    },

    {
        "head": {
            "cmd": SC_GUARDFAIL,
        },
        "body": {
            "msg": "error info"
        }
    },

    {
        "head": {
            "cmd": SC_GUARDQRPIC,
        },
        "body": {
            "path": "pic_path"
        }
    },

    {
        "head": {
            "cmd": SC_GETLISENCE,
        },
        "body": {}
    },

    {
        "head": {
            "cmd": SC_GETAUTHCONTENT,
        },
        "body": {
            "item_count": n;
            "item_array": []
        }
    },

    {
        "head": {
            "cmd": SC_GETVERIFYPICTURE,
        },
        "body": {
            "pic_name": ""
        }
    },

    {
        "head": {
            "cmd": SC_CAPTIONTIP,
        },
        "body": {
            "arg_first": 1
        }
    },

} // Login DATA end

// Login DATA web to host
{

    {
        "head": {
            "cmd": CS_VERIFY_VERIFYCODE,
        },
        "body": {
            "yzm_code": "123",
            "click_cancle": 0
        }
    },

    {
        "head": {
            "cmd": CS_VERIFY_ACCOUNT,
        },
        "body": {
            "record_uin": 1,
            "close_sound": 1
        }
    },

    {
        "head": {
            "cmd": CS_VERIFY_TOKEN,
        },
        "body": {
            "token_str": "str",
            "token_type": 1
        }
    },

    {
        "head": {
            "cmd": CS_SETTEDITFOCUS,
        },
        "body": {
            "type": 0, // 0 帐号框，1 密码框
        }
    }
} // Login DATA end


// Updata DATA host to web
{
    {
        "head": {
            "cmd": SC_DOWNLOADPAGEUI,
        },
        "body": {
            "arg_first": 100,
            "arg_second": ""
        }
    },

    {
        "head": {
            "cmd": SC_UPDATESUCCESS,
        },
        "body": {
            "update_ret": 0, // 是否为灰度升级
            "version": "1.0.0.0"
        }
    }，

    {
        "head": {
            "cmd": SC_UPDATEFAIL,
        },
        "body": {
            "error_code": 738197935,
            "error_info": "msg",
            "url_addr": ""
        }
    }，

    {
        "head": {
            "cmd": SC_VERSIONUPDATEINFO,
        },
        "body": {
            "current_file_name": "",
            "version": "",
            "description": "",
            "branch_name": "",
            "patch_project_name": "",
            "current_file_size": 0,
            "total_file_size": 0,
            "download_speed": 0,
            "download_file_size": 0,
            "total_process": 0,
            "single_process": 0,
            "current_step": 0,
            "mix_process_info": ""
            "ads_json_data": "{...}"
        }
    }，

    {
        "head": {
            "cmd": SC_UPDATE_NOTIFYMESSAGEBOX,
        },
        "body": {
            "notify_type": 0,
            "nitofy_msg": ""
        }
    }
} // Upata DATA end

// Updata DATA web to host
{
    {
        "head": {
            "cmd": CS_START_UPDATE,
        },
        "body": {}
    }，

    {
        "head": {
            "cmd": CS_START_DOWNLOADANDUPDATE,
        },
        "body": {}
    }，

    {
        "head": {
            "cmd": CS_COUNTIUNE_UPDATE,
        },
        "body": {}
    }，

    {
        "head": {
            "cmd": CS_STOP_UPDATE,
        },
        "body": {}
    }
} // Upata DATA end

// Dir DATA hsot to web
{
    {
        "head": {
            "cmd": SC_DIR_NOTIFYMESSAGEBOX,
        },
        "body": {
            "arg_first": 1,
            "arg_second": ""
        }
    },

    {
        "head": {
            "cmd": SC_ASKENTRYFULLSERVER,
        },
        "body": {
            "arg_first": dwArgFirst,
            "arg_second": "szArgSecond"
        }
    },

    {
        "head": {
            "cmd": SC_DIR_STTIMEOUT,
        },
        "body": {
            "arg_first": ""
        }
    },

    {
        "head": {
            "cmd": SC_BCANENTRYSERVER,
        },
        "body": {
            "arg_first": dwArgFirst,
            "arg_second": "szArgSecond"
        }
    },

    {
        "head": {
            "cmd": SC_GETDIRINFOFAIL,
        },
        "body": {}
    },

    {
        "head": {
            "cmd": SC_GETDIRINFOSUCCESS,
        },
        "body": {
            "node_list": [{
                "id": 0,
                "branch_number": 0,
                "current_depth": 0,
                "parent_id": 0,
                "tree_depth": 0,
                "app_data_count": 0,
                "app_data_array": 0,
                "branch_id_count": 0,
                "branch_id_array": 0
            }]
            "node_count": 0,
            "dir_index": 0,
            "isp": 0,
            "rec_node": 0,

            "attr_0": 0,
            "attr_1": 0,

            "bitmap_mask": 0,
            "name": "",
            "game_server_info": '',
            "logical_game_serv": '',
            "server_net_speed": 0,
            "status": '',
            "block_flag": '',
            "max_online": 0,
            "current_online": 0,
            "user_data": 0,

            "connect_url": "",

            "Version": "",
            "gray_flag": ""
        }
    }

} // Dir DATA end

// Dir DATA web to host
{
    {
        "head": {
            "cmd": CS_GET_DIRANDTACCINFO,
        },
        "body": {}
    },
    // {
    // 	"head": {
    // 		"cmd": CS_DETECT_NETSPEED,
    // 	},
    // 	"body":{
    // 		"node_id":0
    // 	}
    // },
    {
        "head": {
            "cmd": CS_ENTER_SERVER,
        },
        "body": {
            "node_id": 0
        }
    }
    // {
    // 	"head": {
    // 		"cmd": CS_BENTER_FULLSERVER,
    // 	},
    // 	"body":{
    // 		"node_id":0
    // 	}
    // },
    // {
    // 	"head": {
    // 		"cmd": CS_DIR_NOTIFYMESSAGERETURN,
    // 	},
    // 	"body":{
    // 		"node_id":0
    // 	}
    // }
} // Dir DATA end


// Launch DATA web to host
{
    {
        "head": {
            "cmd": CS_START_LAUNCHGAME,
        },
        "body": {
            "wechat_bind_not_ask": 1
        }
    },
} // Launch DATA end