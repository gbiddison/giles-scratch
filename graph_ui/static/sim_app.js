/**
 * Created by stonerri on 7/2/15.
 */


var app = angular.module( 'graph_ui_module', [] );

app.factory('WebSocketService', ['$q', '$rootScope', function ($q, $rootScope) {

    var Service = {};           // we return this object
    var callbacks = {};
    var currentCallbackId = 0;
    var ws = undefined;

    function sendRequest(request) {
        var defer = $q.defer();
        var callbackId = getCallbackId();
        callbacks[callbackId] = {
            time: new Date(),
            cb: defer
        };
        request.callback_id = callbackId;
        ws.send(JSON.stringify(request));
        return defer.promise;
    }

    function listener(messageObj) {
        // if this has a specific callback assigned, send to the promise
        if (callbacks.hasOwnProperty(messageObj.callback_id)){
            $rootScope.$apply(callbacks[messageObj.callback_id].cb.resolve(messageObj.result));
            delete callbacks[messageObj.callbackID];
        }
        else
            // else, send to rootscope's switchboard
            $rootScope.switchBoard(messageObj);
    }

    function getCallbackId() {
        currentCallbackId  = (currentCallbackId + 1) % 10000;
        return currentCallbackId;
    }

    Service.initialize = function(){
        var loc = window.location, new_uri;
        new_uri = loc.protocol === "https:" ? new_uri = "wss:" : new_uri = "ws:";

        new_uri += "//" + loc.host;
        new_uri += loc.pathname + "ws";
        console.log(new_uri);

        ws = new WebSocket(new_uri);

        ws.onopen = function () {
            console.log("Socket has been opened!");
            $rootScope.connection_status = 'Connected';
            Service.command('init', '', '', window.location.origin);
        };

        ws.onclose = function(){
            $rootScope.connection_status = 'Disconnected, Click to Connect';
            $rootScope.$apply();
            console.log("Socket closed");
        };

        ws.onmessage = function (message) {
            listener(JSON.parse(message.data));
        };
    };

    Service.command = function(command, payload) {
        var d = {
            command : command,
            payload : payload
        };
        var promise = sendRequest(d);
        return promise;
    };

    return Service;
}]);


/*
    app directive -- resize : seems to get called when the browser is resized
    can attach 'resize' as a directive to any html element eg <div resize />
    but since this touches fabric_canvas, it needs to be an element inside the ng-controller associated <div>
*/
app.directive('resize', function ($window) {
    return function ($scope, element) {
        var w = angular.element($window);
        var changeSize = function() {
            var ctx = document.getElementById("c").getContext("2d");
            ctx.canvas.width = $("#canvaswrap").width()-4;
            ctx.canvas.height = angular.element($window).height() - 300;
        };
        w.bind('resize', function () {
            changeSize();   // when window size gets changed
        });
        changeSize(); // when page loads
    }
})

/*
    the root controller
*/
app.controller('rootController', ['$scope', '$rootScope', '$timeout', 'WebSocketService', '$window',
        function ($scope, $rootScope, $timeout, WebSocketService, $window) {

    console.log('Initialized root controller.');
    $rootScope.connection_status = 'Disconnected, Click to Connect';

    $scope.reconnect = function(){
        WebSocketService.initialize();
    };

    draw_poly = function(ctx, points){
        ctx.beginPath();
        ctx.moveTo(points[0][0], points[0][1]);
        for( var i in points)
        {
            console.log(points[i]);
            ctx.lineTo(points[i][0], points[i][1]);
        }
        ctx.stroke();
    }

    /* for now, sim positions are client side */
    $scope.render_state = function(){
        var ctx = document.getElementById("c").getContext("2d");

        var bug_const = {
            'hdtl':     29,
        	'hdtang':   Math.PI/2,
            'hdbl':     14,
            'hdbang':   Math.PI/2,
            'hdsl':     Math.sqrt(11.0*11 + 22*22),
        	'hdsang':   [Math.atan2(22.0,11.0), Math.atan2(22.0,-11.0)],
        }
        var bug = {   // state
            'x': 0.0,
            'y': 0.0,
            'angle': 0.0,
        }

        var Scale = 10.0;
        var AspR = 1.0;

    	var mouthX = bug.x + bug_const.hdtl * Math.cos(bug.angle + bug_const.hdtang);
	    var mouthY = bug.y + bug_const.hdtl * Math.sin(bug.angle + bug_const.hdtang);
    	var bugx = 0.5 * bug.x * Scale + 0.5;
	    var bugy = 0.5 * bug.y * Scale * AspR + 0.5;
        var temp1 = bug.angle + bug_const.hdsang[0]; // head angle offset
        var temp2 = bug.angle + bug_const.hdsang[1];
        var temp3 = bug.angle + bug_const.hdbang;    // body angle offset

        // calculate bug pts
        var head_points = [[0,0], [0,0], [0,0], [0,0]]
        head_points[0]= [ 0.5 * Scale * mouthX, 0.5 * Scale * mouthY * AspR];
        head_points[1] = [ bugx + (0.5 * Scale * bug_const.hdsl * Math.cos(temp1)), bugy + (0.5 * Scale*AspR * bug_const.hdsl * Math.sin(temp1))]
        head_points[2] = [ bugx + (0.5 * Scale * bug_const.hdbl * Math.cos(temp3)), bugy + (0.5 * Scale*AspR * bug_const.hdbl * Math.sin(temp3))]
        head_points[3] = [ bugx + (0.5 * Scale * bug_const.hdsl * Math.cos(temp2)), bugy + (0.5 * Scale*AspR * bug_const.hdsl * Math.sin(temp2))]

        draw_poly(ctx, head_points);

        //if (bug.mouth)
        //    dc.DrawLine( bugp.head[0],bugp.head[1],bugp.head[4],bugp.head[5]);

        //draw_poly(ctx, 6, body_points);

        // draw antennae
        //for (i=0; i<2; ++i)
        //    dc.DrawLine(bugp.antax[i],bugp.antay[i],bugp.antx[i],bugp.anty[i]);

        // draw cerci
        //for (i=0; i<2; ++i)
        //    dc.DrawLine(bugp.cercax[i],bugp.cercay[i],bugp.cerciX[i],bugp.cerciY[i]);

        // draw legs & feet
        //for (i=0; i<6; ++i)
        //{
        //    dc.DrawLine(bugp.legx[i],bugp.legy[i],bugp.footx[i],bugp.footy[i]);
        //    if (bug.foot[i])
        //        dc.DrawRectangle(bugp.footx[i]-1,bugp.footy[i]-1,max(2.0,Scale*3.0),std::max(2.0,Scale*3.0));
        //}
    }

    $scope.initialize = function(payload){


        $scope.render_state();
    }

    $rootScope.switchBoard = function(message) {
        // console.log(message);

        switch (message.command) {
            case 'init response':
                console.log(message);
                $scope.initialize(message.payload)
                break;

            case 'update':
                for (var key in message.payload) {
                    $scope[key] = value = message.payload[key]; // for updating {{ }} variables, but we should do this more intelligently
                }
                break;

            default:
                console.log('Unhandled command');
                console.log(message);
                break;
        }
        $scope.$apply();
    };

    WebSocketService.initialize();

}]);