var ServerController = {
    create: function() {
        var serverController = {};

        var view = null;

        var isMute = true;

        var serverConfig = null;

        var currServerInfo = null;
        var serverIconName = null;
        var serverIconContainer = null;

        var serverPath = "servers/";

        serverController.initialize = function() {
            view = document.getElementById("server");
            serverIconName = document.getElementById("serverIconName");
            serverIconContainer = document.getElementById("serverIconContainer");

            serverConfig = new Object();
            this.addServerConfig(257, "艾欧尼亚", "1001_NAME.png", "1001.png", "1001.webp");
            this.addServerConfig(513, "祖安", "1002_NAME.png", "1002.png", "1002.webp");
            this.addServerConfig(769, "诺克萨斯", "1003_NAME.png", "1003.png", "1003.webp");
            this.addServerConfig(1025, "班德尔城", "1004_NAME.png", "1004.png", "1004.webp");
            this.addServerConfig(1281, "皮尔特沃夫", "1005_NAME.png", "1005.png", "1005.webp");
            this.addServerConfig(1537, "战争学院", "1006_NAME.png", "1006.png", "1006.webp");
            this.addServerConfig(1793, "巨神峰", "1007_NAME.png", "1007.png", "1007.webp");
            this.addServerConfig(2049, "雷瑟守备", "1008_NAME.png", "1008.png", "1008.webp");
            this.addServerConfig(3073, "钢铁烈阳", "1009_NAME.png", "1009.png", "1009.webp");
            this.addServerConfig(2305, "裁决之地", "1010_NAME.png", "1010.png", "1010.webp");
            this.addServerConfig(2561, "黑色玫瑰", "1011_NAME.png", "1011.png", "1011.webp");
            this.addServerConfig(2817, "暗影岛", "1012_NAME.png", "1012.png", "1012.webp");
            this.addServerConfig(3585, "均衡教派", "1013_NAME.png", "1013.png", "1013.webp");
            this.addServerConfig(3329, "水晶之痕", "1014_NAME.png", "1014.png", "1014.webp");
            this.addServerConfig(3841, "影流", "1025_NAME.png", "1025.png", "1025.webp");
            this.addServerConfig(4097, "守望之海", "1024_NAME.png", "1024.png", "1024.webp");
            this.addServerConfig(4353, "征服之海", "1026_NAME.png", "1026.png", "1026.webp");
            this.addServerConfig(4609, "卡拉曼达", "1027_NAME.png", "1027.png", "1027.webp");
            // this.addServerConfig(4609, "强者世界", "1029_NAME.png", "1029.png", "1029.webp");
            this.addServerConfig(4865, "皮城警备", "1030_NAME.png", "1030.png", "1030.webp");

            this.addServerConfig(258, "比尔吉沃特", "1015_NAME.png", "1015.png", "1015.webp");
            this.addServerConfig(514, "德玛西亚", "1016_NAME.png", "1016.png", "1016.webp");
            this.addServerConfig(770, "弗雷尔卓德", "1017_NAME.png", "1017.png", "1017.webp");
            this.addServerConfig(1026, "无畏先锋", "1018_NAME.png", "1018.png", "1018.webp");
            this.addServerConfig(1282, "恕瑞玛", "1019_NAME.png", "1019.png", "1019.webp");
            this.addServerConfig(1538, "扭曲丛林", "1020_NAME.png", "1020.png", "1020.webp");
            this.addServerConfig(1794, "巨龙之巢", "1032_NAME.png", "1032.png", "1032.webp");

            this.addServerConfig(261, "男爵领域", "1033_NAME.png", "1033.png", "1033.webp");
            this.addServerConfig(517, "峡谷之巅", "1034_NAME.png", "1034.png", "1034.webp");
            this.addServerConfig(0, "试炼之地", "1021_NAME.png", "1021.png", "1021.webp");
            this.addServerConfig(65539, "教育网专区", "1022_NAME.png", "1022.png", "1022.webp");
            this.addServerConfig(65540, "移动专区", "1023_NAME.png", "1023.png", "1023.webp");
        };

        serverController.addServerConfig = function(id, name, nameSource, iconSource, iconSourceAnimation) {
            if (serverConfig && serverConfig[id] == undefined) {
                serverConfig[id] = {
                    id: id,
                    name: name,
                    nameSource: nameSource,
                    iconSource: iconSource,
                    iconSourceAnimation: iconSourceAnimation
                };
            }
        };

        serverController.getServerNameSource = function(id) {
            var serverInfo = serverConfig[id];
            if (serverInfo) {
                return serverPath + serverInfo.nameSource;
            }
            return "";
        };

        serverController.getServerIconSource = function(id) {
            var serverInfo = serverConfig[id];
            if (serverInfo) {
                return serverPath + (isMute ? serverInfo.iconSource : serverInfo.iconSourceAnimation);
            }
            return "";
        };

        serverController.setMute = function(value) {
            if (isMute == value) return;

            isMute = value;
            this.updateMute();
        };

        serverController.selectServer = function(serverInfo) {
            // alert("Server ID : " + serverInfo.server_id);
            currServerInfo = serverInfo;

            if (currServerInfo) {
                this.updateMute();
                TweenMax.to(serverIconContainer, 0, {
                    scale: 1,
                    autoAlpha: 1
                });
                TweenMax.from(serverIconContainer, 0.25, {
                    scale: 0.65,
                    autoAlpha: 0.5
                });
            }
        };

        serverController.updateMute = function() {
            if (currServerInfo) {
                serverIconName.src = this.getServerNameSource(currServerInfo.server_id);
                serverIconContainer.src = this.getServerIconSource(currServerInfo.server_id);
            }
        };

        serverController.show = function(callBack, duration) {
            this.clear();
            if (duration == undefined) duration = 0.5;

            if (view) {
                TweenMax.to(view, duration, {
                    autoAlpha: 1,
                    onComplete: callBack
                })
            }
        };

        serverController.hide = function(callBack, duration) {
            if (duration == undefined) duration = 0.5;

            if (view) {
                TweenMax.to(view, duration, {
                    autoAlpha: 0,
                    onComplete: callBack
                })
            }
        };

        serverController.clear = function() {

        };

        serverController.dispose = function() {

        };

        return serverController;
    }
}