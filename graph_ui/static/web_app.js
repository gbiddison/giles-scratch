/**
 * Created by stonerri on 7/2/15.
 */


var app = angular.module( 'userModule', [] );

app.factory('WebSocketService', ['$q', '$rootScope', function ($q, $rootScope) {

    var Service = {};
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
        else {
            // else, send to rootscope's switchboard
            $rootScope.switchBoard(messageObj);
        }
    }


    function getCallbackId() {
        currentCallbackId += 1;
        if (currentCallbackId > 10000) {
            currentCallbackId = 0;
        }
        return currentCallbackId;
    }

    Service.initialize = function(){

        var loc = window.location, new_uri;
        if (loc.protocol === "https:") {
            new_uri = "wss:";
        } else {
            new_uri = "ws:";
        }
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

app.directive('resize', function ($window) {
    return function (scope, element) {
        var w = angular.element($window);
        var changeHeight = function() {
            scope.fabric_canvas.setHeight(angular.element($window).height() - 300)
        };
        w.bind('resize', function () {
            changeHeight();   // when window size gets changed
        });
        changeHeight(); // when page loads
    }
})

app.controller('rootController', ['$scope', '$rootScope', '$timeout', 'WebSocketService', '$window',
        function ($scope, $rootScope, $timeout, WebSocketService, $window) {

    console.log('Initialized root controller.');
    $rootScope.connection_status = 'Disconnected, Click to Connect';

    $scope.add_node = function(label, x_coord, y_coord) {
        var width = 45;
        var height = 25;

        var rect = new fabric.Rect({
            width: width, height: height,
            originX: 'center',
            originY: 'center',
            fill: '#00f0c0',
            angle: 0
        });

        var text = new fabric.Text(label, {
            originX: 'center',
            originY: 'center',
            fontFamily: 'Helvetica',
            fontSize: 10
        });

        var group = new fabric.Group([rect, text], {
            left: x_coord + 2,
            top: y_coord + 5
        });
        group.label = label;
        group.hasControls = true;
        group.lockUniScaling = group.lockScalingX = group.lockScalingY = true;
        group.lockRotation = true;
        group.on('selected', function () {
            $scope.current_selection = [$scope.fabric_canvas.getActiveObject().label];
            $scope.$apply();
        });

        $scope.fabric_canvas.add(group);
        $scope.all_nodes[label] = group;
    }

    $scope.add_edge = function(edge) {
        $scope.all_edges.push(edge);
    }
    $scope.render_edges = function() {
        // get a buffer where we can draw directly to the canvas on the background layer
        buffer = $scope.buffer = document.createElement('canvas');
        buffer.width = $scope.fabric_canvas.getWidth();
        buffer.height = $scope.fabric_canvas.getHeight();

        ctx = $scope.buffer.getContext('2d');
        ctx.strokeStyle='rgba(0, 0, 255, 0.5)';
        ctx.beginPath();
        for( var i in $scope.all_edges){
            edge = $scope.all_edges[i];
            var start = $scope.all_nodes[edge[0]];
            var end = $scope.all_nodes[edge[1]];
            var start_w = start.getWidth();
            var start_h = start.getHeight();
            var end_h = end.getHeight();
            var x1 = start.getLeft() + start_w;
            var y1 = start.getTop() + start_h / 2;
            var x2 = end.getLeft();
            var y2 = end.getTop() + end_h / 2;

            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
        }
        ctx.stroke();

        var img = new fabric.Image( buffer, { left:0, top:0, angle:0});
        $scope.fabric_canvas.setBackgroundImage(img)
    }


    $scope.create_viz = function () {

        // create a wrapper around native canvas element (with id="c")
        $scope.fabric_canvas = new fabric.Canvas('c', {});
        $scope.fabric_canvas.setWidth($("#canvaswrap").width()-4);
        $scope.fabric_canvas.setHeight(angular.element($window).height() - 300);

        $scope.fabric_canvas.on('selection:created', function () {
            var select_array = [];
            var selection = $scope.fabric_canvas.getActiveGroup().getObjects();
            for (var i in selection) {
                console.log(i, selection[i].label);
                select_array.push({"label":selection[i].label});
            }
            $scope.current_selection = select_array;
            $scope.$apply();
        });

        $scope.fabric_canvas.on('selection:cleared', function () {
            $scope.current_selection = [];
            $scope.$apply();
        });
        $scope.fabric_canvas.on('object:moving', function(e) {
            $scope.render_edges();
        });

        $scope.fabric_canvas.selection = true;

        $scope.all_nodes = {};  // keyed by node name
        $scope.all_edges = [];  // each entry is a pair of edges ... maybe not a good key?  dunno

        // raw canvas drawing alternatively
        /*
        var canvas = document.getElementById('c');
        var ctx = canvas.getContext('2d');
        canvas.width = $("#canvaswrap").width()-4;

        ctx.beginPath();
        ctx.moveTo(0,0);
        ctx.lineTo(ctx.canvas.width, 0);
        ctx.lineTo(ctx.canvas.width, ctx.canvas.height);
        ctx.lineTo(0, ctx.canvas.height);
        ctx.lineTo(0, 0);

        ctx.moveTo(0,0);
        ctx.lineTo(ctx.canvas.width, ctx.canvas.height);
        ctx.stroke();
        */
    };

    $scope.create_viz();


    $scope.reconnect = function(){
            WebSocketService.initialize();
    };

    $scope.init_nodes = function(payload){
        width = $scope.fabric_canvas.getWidth();
        height = $scope.fabric_canvas.getHeight();
        if('nodes' in payload){
            for(var node in payload.nodes){
                x = payload.nodes[node].x * width;
                y = payload.nodes[node].y * height;
                $scope.add_node(node, x, y)
            }
        }
        if('edges' in payload){
            for(var edge in payload.edges)
            $scope.add_edge(payload.edges[edge])
            $scope.render_edges()
        }
    }

    $rootScope.switchBoard = function(message) {

        // console.log(message);

        switch (message.command) {
            case 'init response':
                console.log(message);
                $scope.init_nodes(message.payload)
                break;

            case 'update':

                for (var key in message.payload) {
                    $scope[key] = value = message.payload[key];

                    if( key in $scope.all_nodes){
                        node = $scope.all_nodes[key].getObjects()[0];
                        node.setFill("rgb(0, 240," + value[2] + ')');
                    }
                }

                // console.log(message);

                break;

            default:
                console.log('Unhandled command');
                console.log(message);
                break;
        }

        $scope.fabric_canvas.renderAll();
        $scope.$apply();
    };

    WebSocketService.initialize();

}]);