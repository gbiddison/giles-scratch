/**
 * Created by stonerri on 7/2/15.
 */

String.prototype.in_list=function(list){
   return ( list.indexOf(this.toString()) != -1)
}

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
            $scope.fabric_canvas.setWidth($("#canvaswrap").width()-4);
            $scope.fabric_canvas.setHeight(angular.element($window).height() - 300)

            $scope.rescale_nodes();
            $scope.render_edges();
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

    /*
        add a node item to the fabric canvas; a node has coordinates and a label
        we are also interested in whether the node has incoming or outgoing edges,
        so that we can represent terminal nodes with a different shape

        node coords are represented from 0.0 to 1.0, in order to be view scale independent
    */
    $scope.add_node = function(label, x_coord, y_coord, is_input, is_output) {
        var width = $scope.fabric_canvas.getWidth();
        var height = $scope.fabric_canvas.getHeight();
        var size = 0.05 * Math.min(width, height);
        var x = x_coord * width;
        var y = y_coord * height;

        var node = null, fill = 0;
        if (is_input){
            node = new fabric.Rect({
                width: size, height: size,
                originX: 'center', originY: 'center',
                fill: '#ffffff',
                stroke: '#00f0c0'
            });
            fill = new fabric.Rect({
                width: 0.1, height: 0.1,
                originX: 'center', originY: 'center',
                fill: '#00f0c0'
            });
        }else if(is_output){
            node = new fabric.Triangle({
                width: size, height: size,
                originX: 'center', originY: 'center',
                fill: '#ffffff',
                stroke: '#00f0c0',
                angle: 90.0
            });
            fill = new fabric.Triangle({
                width: 0.1, height: 0.1,
                originX: 'center', originY: 'center',
                fill: '#00f0c0',
                angle: 90.0
            });
        }else{
            node = new fabric.Circle({
                radius: size/2.0,
                originX: 'center', originY: 'center',
                fill: '#ffffff',
                stroke: '#00f0c0'
            });
            fill = new fabric.Circle({
                radius: 0.1,
                originX: 'center', originY: 'center',
                fill: '#00f0c0'
            });
        }

        var text = new fabric.Text(label, {
            originX: 'center',
            originY: 'center',
            fontFamily: 'Helvetica',
            fontSize: 10
        });

        var group = new fabric.Group([node, fill, text], {
            left: x,
            top: y
        });
        group.label = label;
        group.hasControls = true;
        group.lockUniScaling = group.lockScalingX = group.lockScalingY = true;
        group.lockRotation = true;
        group.set({ width: size, height: size});
        group.unscaled_x = x_coord;   // save unscaled coords for rescaling later
        group.unscaled_y = y_coord;

        group.on('selected', function () {
            $scope.current_selection = [$scope.fabric_canvas.getActiveObject().label];
            //$scope.$apply();
            $scope.render_edges();
        });


        $scope.fabric_canvas.add(group);
        $scope.all_nodes[label] = group;
    }

    /*
        rescale all the nodes to a new canvas size
    */
    $scope.rescale_nodes = function(){
        var width = $scope.fabric_canvas.getWidth();
        var height = $scope.fabric_canvas.getHeight();
        var size = 0.05 * Math.min(width, height);
        for(var name in $scope.all_nodes){
            var group = $scope.all_nodes[name];
            var rect = group.item(0);
            var fill = group.item(1);
            var label = group.item(2);
            var factor = size / rect.getWidth();

            rect.set({ width: size, height: size, radius: size/2.0});
            fill.set({ width: fill.getWidth() * factor, height: fill.getHeight() * factor, radius: (fill.getWidth() * factor)/2.0});
            group.set({ width: size, height: size});
            group.set({ left: group.unscaled_x * width, top: group.unscaled_y * height});
            group.setCoords(); // reset location of hit box
        }
        $scope.fabric_canvas.renderAll();
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
        var unselected = 'rgba(0, 0, 255, 0.10)';
        var outgoing = 'rgba(0, 255, 47, 0.90)';
        var incoming = 'rgba(255, 105, 180, 0.90)';

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

            var cur = $scope.current_selection;
            ctx.beginPath();
            ctx.strokeStyle = (cur == edge[0]) ? outgoing : (cur == edge[1]) ? incoming : unselected;

            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }

        var img = new fabric.Image( buffer, { left:0, top:0, angle:0});
        $scope.fabric_canvas.setBackgroundImage(img)
    }

    $scope.create_viz = function () {

        // create a wrapper around native canvas element (with id="c")
        $scope.fabric_canvas = new fabric.Canvas('c', {});

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

        // redraw *all* the edges when any node moves; yes not optimal but seems quick enough
        $scope.fabric_canvas.on('object:moving', function(e) {
            // limit object dragging to canvas bounds
            var obj = e.target;
            obj.setCoords();
            // top-left  corner
            if(obj.getBoundingRect().top < 0 || obj.getBoundingRect().left < 0){
                obj.top = Math.max(obj.top, obj.top-obj.getBoundingRect().top);
                obj.left = Math.max(obj.left, obj.left-obj.getBoundingRect().left);
            }
            // bot-right corner
            if(obj.getBoundingRect().top+obj.getBoundingRect().height  > obj.canvas.height || obj.getBoundingRect().left+obj.getBoundingRect().width  > obj.canvas.width){
                obj.top = Math.min(obj.top, obj.canvas.height-obj.getBoundingRect().height+obj.top-obj.getBoundingRect().top);
                obj.left = Math.min(obj.left, obj.canvas.width-obj.getBoundingRect().width+obj.left-obj.getBoundingRect().left);
            }

            $scope.render_edges();
        });

        $scope.fabric_canvas.selection = false; // no group selection

        $scope.all_nodes = {};  // keyed by node name
        $scope.all_edges = [];  // each entry is a pair of edges ... maybe not a good key?  dunno
    };

    $scope.create_viz();

    $scope.reconnect = function(){
        WebSocketService.initialize();
    };

    $scope.init_nodes = function(payload){
        // clear out any existing state - server is pushing us a completely new state
        $scope.all_nodes = {};
        $scope.all_edges = [];
        $scope.fabric_canvas.clear();

        for(var edge in payload.edges)
            $scope.add_edge(payload.edges[edge]);

        for(var node in payload.nodes){
            $scope.add_node(node,
                payload.nodes[node].x,
                payload.nodes[node].y,
                node.in_list(payload.inputs),
                node.in_list(payload.outputs));
        }
        $scope.render_edges()
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
                    value = message.payload[key];
                    // if key is a neuron, value is neuron firing frequency
                    // render firing frequency as % fill
                    if( key in $scope.all_nodes){
                        value = message.payload[key];
                        node = $scope.all_nodes[key].item(0);
                        fill = $scope.all_nodes[key].item(1);
                        fill.set({width: node.getWidth() * value, height: node.getHeight() * value, radius: node.get('radius') * value});
                    }else
                        // otherwise interpret the value as a scope key
                        // for updating {{ }} variables
                        $scope[key] = value;
                }
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