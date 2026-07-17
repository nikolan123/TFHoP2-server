package {
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.events.NetStatusEvent;
    import flash.events.TimerEvent;
    import flash.media.SoundTransform;
    import flash.media.Video;
    import flash.net.NetConnection;
    import flash.net.NetStream;
    import flash.net.URLLoader;
    import flash.net.URLRequest;
    import flash.system.Security;
    import flash.utils.Timer;

    [SWF(width="640", height="360", frameRate="30", backgroundColor="#000000")]
    public class ApiPlayer extends Sprite {
        private var connection:NetConnection;
        private var stream:NetStream;
        private var video:Video;
        private var duration:Number = 0;
        private var playerState:int = -1;
        private var muted:Boolean = false;
        private var pendingSeek:Number = 0;
        private var readyTimer:Timer;
        private var diagnosticLoaders:Array = [];

        public function ApiPlayer() {
            Security.allowDomain("*");
            Security.allowInsecureDomain("*");

            video = new Video(640, 360);
            video.smoothing = true;
            addChild(video);

            connection = new NetConnection();
            connection.connect(null);

            stream = new NetStream(connection);
            stream.client = {
                onMetaData: onMetaData,
                onPlayStatus: onPlayStatus
            };
            stream.addEventListener(NetStatusEvent.NET_STATUS, onNetStatus);
            video.attachNetStream(stream);

            notify("root-bound");
            readyTimer = new Timer(300, 1);
            readyTimer.addEventListener(TimerEvent.TIMER_COMPLETE, dispatchReady);
            readyTimer.start();
        }

        private function dispatchReady(event:TimerEvent):void {
            notify("ready");
            dispatchEvent(new Event("onReady"));
        }

        public function loadVideoById(videoId:String, startSeconds:Number = 0, suggestedQuality:String = "large"):void {
            pendingSeek = startSeconds;
            duration = 0;
            setState(3);
            notify("load-" + videoId);
            stream.play(getOrigin() + "/youtube/" + videoId + ".mp4");
            dispatchEvent(new PlayerEvent("onPlaybackQualityChange", suggestedQuality));
        }

        public function playVideo():void {
            stream.resume();
            setState(1);
        }

        public function pauseVideo():void {
            stream.pause();
            setState(2);
        }

        public function seekTo(seconds:Number, allowSeekAhead:Boolean = true):void {
            stream.seek(seconds);
        }

        public function getCurrentTime():Number {
            return stream.time;
        }

        public function getDuration():Number {
            return duration;
        }

        public function getPlayerState():int {
            return playerState;
        }

        public function setSize(playerWidth:Number, playerHeight:Number):void {
            video.width = playerWidth;
            video.height = playerHeight;
        }

        public function mute():void {
            muted = true;
            applyVolume();
        }

        public function unMute():void {
            muted = false;
            applyVolume();
        }

        public function isMuted():Boolean {
            return muted;
        }

        private function applyVolume():void {
            stream.soundTransform = new SoundTransform(muted ? 0 : 1);
        }

        private function getOrigin():String {
            var match:Array = loaderInfo.url.match(/^(https?:\/\/[^\/]+)/);
            return match ? match[1] : "";
        }

        private function notify(eventName:String):void {
            try {
                var loader:URLLoader = new URLLoader();
                diagnosticLoaders.push(loader);
                loader.load(new URLRequest(getOrigin() + "/youtube/player-event/" + eventName));
            } catch (error:Error) {
            }
        }

        private function onMetaData(info:Object):void {
            if (info.duration != null) {
                duration = Number(info.duration);
            }
        }

        private function onPlayStatus(info:Object):void {
            if (info.code == "NetStream.Play.Complete") {
                setState(0);
            }
        }

        private function onNetStatus(event:NetStatusEvent):void {
            switch (event.info.code) {
                case "NetStream.Play.Start":
                    if (pendingSeek > 0) {
                        stream.seek(pendingSeek);
                        pendingSeek = 0;
                    }
                    setState(1);
                    break;
                case "NetStream.Play.Stop":
                    setState(0);
                    break;
                case "NetStream.Pause.Notify":
                    setState(2);
                    break;
                case "NetStream.Unpause.Notify":
                case "NetStream.Buffer.Full":
                    setState(1);
                    break;
                case "NetStream.Buffer.Empty":
                    if (playerState != 0 && playerState != 2) {
                        setState(3);
                    }
                    break;
                case "NetStream.Play.StreamNotFound":
                    dispatchEvent(new PlayerEvent("onError", 100));
                    break;
            }
        }

        private function setState(state:int):void {
            if (playerState == state) {
                return;
            }
            playerState = state;
            dispatchEvent(new PlayerEvent("onStateChange", state));
        }
    }
}

import flash.events.Event;

internal class PlayerEvent extends Event {
    public var data:*;

    public function PlayerEvent(type:String, data:*) {
        super(type, false, false);
        this.data = data;
    }

    override public function clone():Event {
        return new PlayerEvent(type, data);
    }
}
