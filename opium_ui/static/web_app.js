/**
 * Created by gbiddison on 7/21/15.
 */

var app = angular.module( 'opium_ui_app', ['ngMaterial', 'ngMdIcons'] );

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
        }else
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
        }

        ws.onclose = function(){
            $rootScope.connection_status = 'Disconnected, Click to Connect';
            $rootScope.$apply();
            console.log("Socket closed");
        }

        ws.onmessage = function (message) {
            listener(JSON.parse(message.data));
        }
    }

    Service.command = function(command, payload) {
        var d = {
                    command : command,
                    payload : payload
                };
        var promise = sendRequest(d);
        return promise;
    }

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
            // TODO do your resizing here
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

    $scope.selected_work = undefined;
    $scope.work_orders = {};
    /*
        eg:     { "work_id": ["plate instances"],
                  "ABCDEF123": ["plate 1", "plate 2"],
                  "ASDFAS123": ["plate 3"],
                  "FOOFOO881": ["plate 4"]};
    */


    /* reconnect to web sockets / python code --> attach to eg ng-click in an html element */
    $scope.reconnect = function(){
        WebSocketService.initialize();
    }

    $scope.get_work_details = function(work){
        $scope.selected_work = work;
    }


    $rootScope.switchBoard = function(message) {
        // console.log(message);

        switch (message.command) {
            case 'init response':
                console.log(message);
                // TODO -- initialize client state
                $scope.work_orders = message.payload;
                break;

            case 'update':
                // TODO -- periodic update client state
                $scope.work_orders = message.payload;
                break;

            default:
                console.log('Unhandled command');
                console.log(message);
                break;
        }
        $scope.$apply();
    }

    WebSocketService.initialize();
}]);