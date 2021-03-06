/**
 * Created by gbiddison on 7/21/15.
 */

var app = angular.module( 'opium_ui_app', ['ngMaterial', 'ngMdIcons'] );

app.factory('WebSocketService', ['$q', '$rootScope', function ($q, $rootScope) {

    var Service = {};           // we return this object
    var callbacks = {};
    var currentCallbackId = 0;
    var ws = undefined;
7
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

    $scope.display_mode = null;

    $scope.selected_factory = null;
    $scope.factories = {};

    $scope.selected_work = null;
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
    };

    $scope.get_work_details = function(work){
        $scope.display_mode = "work"
        $scope.selected_work = work;
        $scope.set_session_variable("selected_work", work);
    };

    $scope.get_factory_details = function(factory){
        $scope.display_mode = "factory"
        $scope.selected_factory = factory;
        $scope.set_session_variable("selected_factory", factory);
    };

    $scope.set_session_variable = function(key, value){
        if(!value){
            $window.sessionStorage.removeItem(key);
            return;
        }
        $window.sessionStorage.setItem(key, value);
        console.log("sessionStorage['" + key + "'] == '" + value +"'");
    };

    $scope.get_session_variable = function(key){
        var value = $window.sessionStorage.getItem(key);
        console.log("sessionStorage['" + key + "'] was '" + value +"'");
        return value;
    };

    $scope.is_empty =  function(obj){
        for(var k in obj)
            if(obj.hasOwnProperty(k)) return false;
        return true;
    };

    $rootScope.switchBoard = function(message) {
        // console.log(message);

        switch (message.command) {
            case 'init response':
                console.log(message);
                $scope.work_orders = message.payload.work;
                $scope.factories = message.payload.factories;
                if( !$scope.work_orders) {
                    console.log("no work!")
                } else {
                    var last_selected_work = $scope.get_session_variable("selected_work");
                    if (last_selected_work) {
                        console.log("selected_work exists")
                        if (last_selected_work in $scope.work_orders) {
                            console.log("restoring selected work")
                            $scope.selected_work = last_selected_work;
                        } else {
                            console.log("clearing selected work")
                            $scope.set_session_variable("selected_work", null);
                        }
                    } else
                        console.log("no selected_work")
                }
                if( !$scope.factories) {
                    console.log("no factories!")
                } else {
                    var last_selected_factory = $scope.get_session_variable("selected_factory");
                    if (last_selected_factory) {
                        console.log("selected_factory exists")
                        if (last_selected_factory in $scope.factories) {
                            console.log("restoring selected factory")
                            $scope.selected_factory = last_selected_factory;
                        } else {
                            console.log("clearing selected factory")
                            $scope.set_session_variable("selected_factory", null);
                        }
                    } else
                        console.log("no selected_factory")
                }
                break;

            case 'update':
                $scope.work_orders = message.payload.work;
                $scope.factories = message.payload.factories;
                console.log('work: ' + $scope.work_orders);
                console.log('factories: ' + $scope.factories);
                if($scope.selected_work && $scope.is_empty($scope.work_orders)) {
                    console.log("out of work, clearing selection");
                    $scope.selected_work = null;
                    $scope.set_session_variable("selected_work", null);
                }
                if($scope.selected_factory && $scope.is_empty($scope.factories)) {
                    console.log("out of factories, clearing selection");
                    $scope.selected_factory = null;
                    $scope.set_session_variable("selected_factory", null);
                }
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