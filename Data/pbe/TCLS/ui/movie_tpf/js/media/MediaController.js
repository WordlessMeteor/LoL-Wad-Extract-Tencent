var MediaController = {
    create: function() {
        var mediaController = {};

        var isMute = true;

        //0-更新 1-登录 2-选服
        var currType = 0;
        var nextType = 0;

        var music = null;
        var loginVideo = null;
        var serverVideo = null;

        var loginMusicPath = "./music/loginSound.mp3";
        var loginVideoPath = "./video/loginPage.webm";

        var serverMusicPath = "./music/serverSound.mp3";
        var serverVideoPath = "./video/serverPage.webm";

        function playMedia(target) {
            if (target) {
                var playPromise = target.play();
                if (playPromise != undefined) {
                    playPromise.then(function() {

                    }).catch(function(e) {})
                }
            }
        }

        function stopMedia(target) {
            if (target) {
                target.currentTime = 0;
                target.pause();
            }
        }

        function showVideo(duration) {
            var target = getVideo(currType);
            stopMedia(target);

            currType = nextType;

            var target = getVideo(currType);
            if (target) {
                showTarget(target, true, duration);
            }

            mediaController.refreshMusic();
            mediaController.updateMute();
        }

        function hideVideo(duration) {
            var target = getVideo(currType);
            if (target) {
                showTarget(target, false, duration, showVideo);
            } else {
                showVideo(duration);
            }
        }

        function showTarget(target, isShow, duration, onCall) {
            if (duration == undefined) duration = 0.5;
            if (isShow) {
                TweenMax.to(target, duration, {
                    autoAlpha: 1,
                    onComplete: onCall
                });
            } else {
                TweenMax.to(target, duration, {
                    autoAlpha: 0,
                    onComplete: onCall
                });
            }
        }

        function getVideo(type) {
            switch (type) {
                case 1: {
                    break;
                }
                case 2: {
                    return loginVideo;
                }
                case 3: {
                    return serverVideo;
                }
            }
            return null;
        }

        function getMusicPath(type) {
            var path = "";
            switch (type) {
                case 1: {
                    path = loginMusicPath;
                    break;
                }
                case 2: {
                    path = loginMusicPath;
                    break;
                }
                case 3: {
                    path = serverMusicPath;
                    break;
                }
                default: {
                    path = loginMusicPath;
                    break;
                }
            }
            return path;
        }

        mediaController.initialize = function() {
            music = document.getElementById("music");
            loginVideo = document.getElementById("loginVideo");
            serverVideo = document.getElementById("loginVideo");

            music = document.getElementById("music");
            loginVideo = document.getElementById("loginVideo");
            serverVideo = document.getElementById("loginVideo");

            showTarget(loginVideo, false, 0);
            showTarget(serverVideo, false, 0);

            this.refreshMusic();
            this.refreshVideo();
            this.updateMute();
        };

        mediaController.setMute = function(value) {
            isMute = value;
            this.updateMute();
        };

        mediaController.enter = function(type) {
            nextType = type;
            hideVideo();
        };

        mediaController.refreshMusic = function() {
            if (music) {
                music.src = getMusicPath(currType);
                music.pause();
                music.load();
            }
        };

        mediaController.refreshVideo = function() {
            if (loginVideo) {
                loginVideo.src = loginVideoPath;
                loginVideo.pause();
                loginVideo.load();
            }
            if (serverVideo) {
                serverVideo.src = serverVideoPath;
                serverVideo.pause();
                serverVideo.load();
            }
            this.updateMute();
        };

        mediaController.updateMute = function() {
            var video = getVideo(currType);

            if (isMute == true) {
                stopMedia(video);
                stopMedia(music);
            } else {
                playMedia(video);
                playMedia(music);
            }
        };

        return mediaController;
    }
};