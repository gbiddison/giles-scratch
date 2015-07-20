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

    $scope.draw_poly = function(ctx, points){
        ctx.beginPath();
        ctx.moveTo(points[0][0], points[0][1]);
        for(var i in points){
            //console.log(points[i]);
            ctx.lineTo(points[i][0], points[i][1]);
        }
        ctx.closePath();
        ctx.stroke();
    }

    $scope.draw_lines = function(ctx, from_points, to_points){
        ctx.beginPath();
        for(var i in from_points){
            ctx.moveTo(from_points[i][0], from_points[i][1]);
            ctx.lineTo(to_points[i][0], to_points[i][1]);
        }
        ctx.stroke();
    }

    $scope.transform = function(points, translate_x, translate_y, radians, scale){
        radians = -(radians + Math.PI/2.0); // to get counter-clockwise rotation, orientated 0.0 = right facing
        var result = points.slice(); // copy array
        for(var i in points){
            var x0 = points[i][0];
            var y0 = points[i][1];
            var x = x0;
            var y = y0;

            x = scale * (x0 * Math.cos(radians) - y0 * Math.sin(radians)) + translate_x;
            y = scale * (x0 * Math.sin(radians) + y0 * Math.cos(radians)) + translate_y;
            result[i] = [x, y];
        }
        return result;
    }

    /* for now, sim positions are client side */
    $scope.render_state = function(){
        var ctx = document.getElementById("c").getContext("2d");
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

        var bug = $scope.bug;
        var x = bug.x + ctx.canvas.width/2.;
        var y = bug.y + ctx.canvas.height/2.;
        var scale = 0.5;

        //draw head
        $scope.draw_poly(ctx, $scope.transform(bug.head_points, x, y, bug.angle, scale));
        //if (bug.mouth)
        //    dc.DrawLine( bugp.head[0],bugp.head[1],bugp.head[4],bugp.head[5]);

        // draw body
        $scope.draw_poly(ctx, $scope.transform(bug.body_points, x, y, bug.angle, scale));

        // draw antennae
        $scope.draw_lines(ctx, $scope.transform(bug.anta_points, x, y, bug.angle, scale),
                               $scope.transform(bug.antb_points, x, y, bug.angle, scale));
        // draw cerci
        $scope.draw_lines(ctx, $scope.transform(bug.cera_points, x, y, bug.angle, scale),
                               $scope.transform(bug.cerb_points, x, y, bug.angle, scale));

        // draw legs & feet
        $scope.draw_lines(ctx, $scope.transform(bug.leg_points, x, y, bug.angle, scale),
                               $scope.transform(bug.foot_points, x, y, bug.angle, scale));
        // draw foot down pad
        //    if (bug.foot[i])
        //        dc.DrawRectangle(bugp.footx[i]-1,bugp.footy[i]-1,max(2.0,Scale*3.0),std::max(2.0,Scale*3.0));
        //
    }

    $scope.initialize = function(payload){
        $scope.initialize_bug();
        $scope.inputs = payload.inputs;
        $scope.outputs = payload.outputs;
    }

    $scope.initialize_bug = function(){
        var bug_const = {
            // HEAD consts
            'hdtl':     29,
        	'hdtang':   Math.PI/2,
            'hdbl':     14,
            'hdbang':   Math.PI/2,                                          // body angle offset
            'hdsl':     Math.sqrt(11.0*11 + 22*22),
        	'hdsang':   [Math.atan2(22.0,11.0), Math.atan2(22.0,-11.0)],    // head angle offset

            // BODY consts
            'btl':      Math.sqrt(6.0*6 + 18*18),
            'btang':    [Math.atan2(18.0,6), Math.atan2(18.0,-6)],
            'bmang':    [0, Math.PI],
            'bbang':    [Math.atan2(-30.0,6), Math.atan2(-30.0,-6)],
            'bml':      12,
            'bbl':      Math.sqrt(6.0*6 + 30*30),

            // LEG consts
            'attl':     [Math.sqrt(8.0*8 + 15*15), 12, Math.sqrt(8.0*8 + 24*24), Math.sqrt(8.0*8 + 15*15), 12, Math.sqrt(8.0*8 + 24*24)],
            'attang':   [Math.atan2(15.0,8.0), 0., Math.atan2(-24.0,8.0), Math.atan2(15.0,-8.0), Math.PI, 2*Math.PI + Math.atan2(-24.0,-8.0)],
            'legl':     [17, 15, 17, 17, 15, 17],

            // ANTENNA consts
        	'antl':     Math.sqrt(30.0*30 + 65*65),
        	'antang':   [Math.atan2(65.0,30), Math.atan2(65.0,-30)],
            'antbl':    Math.sqrt(6.0*6 + 26*26),
            'antbang':  [Math.atan2(26.0,6), Math.atan2(26.0,-6)],

            // CERCI consts
            'cercl':    Math.sqrt(34.0*34 + 8*8),
            'cercang':  [Math.atan2(-34.0,8), Math.atan2(-34.0,-8)],
            'cerbl':    Math.sqrt(2.0*2 + 30*30),
            'cerbang':  [Math.atan2(-30.0,2), Math.atan2(-30.0,-2)],
        }

        var bug = {   // state
            'x': 0.0,
            'y': 0.0,
            'angle': 0.0, // zero is straight right, pi is straight left, counter-clockwise rotations
            'legang':   [0., 0., 0., Math.PI, Math.PI, Math.PI],
            'last_mouth': false,
            'mouth': false,
            'leg': { 'L1': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'L2': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'L3': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'R1': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'R2': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'R3': {'backward_force':0., 'forward_force':0., 'lateral_force':0.}
                   },
            'foot': {'L1':true, 'L2':true, 'L3':true, 'R1':true, 'R2':true, 'R3':true},

            'head_points': [[0,0], [0,0], [0,0], [0,0]],
            'body_points': [[0,0], [0,0], [0,0], [0,0], [0,0]],
            'leg_points':  [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0]],
            'foot_points': [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0]],
            'anta_points': [[0,0], [0,0]],
            'antb_points': [[0,0], [0,0]],
            'cera_points': [[0,0], [0,0]],
            'cerb_points': [[0,0], [0,0]],

        }
    	var mouthX = bug_const.hdtl * Math.cos(bug_const.hdtang);
	    var mouthY = bug_const.hdtl * Math.sin(bug_const.hdtang);

        // calculate bug pts
        var head_points = bug.head_points;
        head_points[0]= [mouthX, mouthY];
        head_points[1] = [bug_const.hdsl * Math.cos(bug_const.hdsang[0]), bug_const.hdsl * Math.sin(bug_const.hdsang[0])];
        head_points[2] = [bug_const.hdbl * Math.cos(bug_const.hdbang),    bug_const.hdbl * Math.sin(bug_const.hdbang)];
        head_points[3] = [bug_const.hdsl * Math.cos(bug_const.hdsang[1]), bug_const.hdsl * Math.sin(bug_const.hdsang[1])];

        var body_points = bug.body_points;
        body_points[0] = [bug_const.btl * Math.cos(bug_const.btang[0]), bug_const.btl * Math.sin(bug_const.btang[0])];
        body_points[1] = [bug_const.bml * Math.cos(bug_const.bmang[0]), bug_const.bml * Math.sin(bug_const.bmang[0])];
        body_points[2] = [bug_const.bbl * Math.cos(bug_const.bbang[0]), bug_const.bbl * Math.sin(bug_const.bbang[0])];
        body_points[3] = [bug_const.bbl * Math.cos(bug_const.bbang[1]), bug_const.bbl * Math.sin(bug_const.bbang[1])];
        body_points[4] = [bug_const.bml * Math.cos(bug_const.bmang[1]), bug_const.bml * Math.sin(bug_const.bmang[1])];
        body_points[5] = [bug_const.btl * Math.cos(bug_const.btang[1]), bug_const.btl * Math.sin(bug_const.btang[1])];

        var leg_points = bug.leg_points;    // we draw from "leg" to "foot"
        var foot_points = bug.foot_points;
        for(var i=0; i<6; ++i){
            leg_points[i] = [bug_const.attl[i] * Math.cos(bug_const.attang[i]),
                             bug_const.attl[i] * Math.sin(bug_const.attang[i])];

            foot_points[i] = [leg_points[i][0] + bug_const.legl[i] * Math.cos(bug.legang[i]),
                              leg_points[i][1] + bug_const.legl[i] * Math.sin(bug.legang[i])];
        }

        var anta_points = bug.anta_points;  // we draw from 'a' to 'b'
        var antb_points = bug.antb_points;
        var cera_points = bug.cera_points;
        var cerb_points = bug.cerb_points;
        for(var i=0; i<2; ++i){
            anta_points[i] = [bug_const.antbl * Math.cos(bug_const.antbang[i]),
                              bug_const.antbl * Math.sin(bug_const.antbang[i])];
            antb_points[i] = [bug_const.antl * Math.cos(bug_const.antang[i]),
                              bug_const.antl * Math.sin(bug_const.antang[i])];
            cera_points[i] = [bug_const.cerbl * Math.cos(bug_const.cerbang[i]),
                              bug_const.cerbl * Math.sin(bug_const.cerbang[i])];
            cerb_points[i] = [bug_const.cercl * Math.cos(bug_const.cercang[i]),
                              bug_const.cercl * Math.sin(bug_const.cercang[i])];
        }

	    $scope.bug = bug;
        $scope.render_state();
    }

    $scope.update_output = function(node, value) {
        var bug = $scope.bug;
        var backward = ["STL1", "STL2", "STL3",  // force backward 50
                        "STR1", "STR2", "STR3"];
        var forward  = ["SWL1", "SWL2", "SWL3",  // force forward 50
                        "SWR1", "SWR2", "SWR3"];
        var lateral  = ["LEL1", "LEL2",          // force lateral 7
                        "LER1", "LER2"];

        var foot = ["FOOTL1", "FOOTL2", "FOOTL3", // state, true > 0
                    "FOOTR1", "FOOTR2", "FOOTR3"];
        var mouth = ["FOMC"]; // state --> output is MO though wtf, true > 0.5

        if( node.in_list(mouth))
        {
            bug.last_mouth = bug.mouth;
            bug.mouth = value > 0.5;
        }
        else if( node.in_list(foot))
        {
            var foot_index = node.slice(-2); // eg "L1"
            bug.foot[foot_index] = value > 0;
        }
        else
        {
            var leg_index = node.slice(-2); // eg "L1"
            if( node.in_list(backward))
                bug.leg[leg_index].backward_force = 50. * value;
            else if( node.in_list(forward))
                bug.leg[leg_index].forward_force = 50. * value;
            else if( node.in_list(lateral))
                bug.leg[leg_index].lateral_force = 7. * value;
        }
    }

    $scope.calculate_state = function() {
        var bug = $scope.bug;
        var leg = bug.leg; // alias for brevity
        var TIMECONSTANT = 1.0 / 200.0; // seconds per simulated time step
        var DT = TIMECONSTANT;
        var TWOPI = 2.0*Math.PI;

        // calculate bug's translational velocity
        var d = 0.;
        for(var i in bug.foot) // sum forces of legs that are down
            if( bug.foot[i])
                d += leg[i].backward_force - leg[i].forward_force;
        d = d/2.; //(adjustable!) originally d/2.0

        // calculate bug's angular velocity
        var f = bug.foot['L1'] * leg['L1'].lateral_force - bug.foot['R1'] * leg['R1'].lateral_force;
        f = f/6.; // (adjustable!) (5 to 6)  original f/6

        var bugx = bug.x - Math.sin(bug.angle) * d * DT;
        var bugy = bug.y + Math.cos(bug.angle) * d * DT;

        // calc sideways force
        d = bug.foot['L2'] * leg['L2'].lateral_force - bug.foot['R2'] * leg['R2'].lateral_force;
        d = 2. * d;  // (adjustable!) (20 to 2)

        bugx -= Math.cos(bug.angle) * d * DT;
        bugy -= Math.sin(bug.angle) * d * DT;
        bug.angle += f * DT;

        if (bug.angle < 0)                 // trig!!!
            bug.angle = TWOPI + bug.angle;
        if (bug.angle >= TWOPI)
            bug.angle = bug.angle - TWOPI;

        /*for(int i=0; i<2; ++i) // calculate bug.antenna & cercus tip positions
        {
            bug.antennaX[i] = bugx + bug_const.antl * Math.cos(bug.angle + bug_const.antang[i]);
            bug.antennaY[i] = bugy + bug_const.antl * Math.sin(bug.angle + bug_const.antang[i]);
            bug.cerciX[i] = bugx + bug_const.cercl * Math.cos(bug.angle + bug_const.cercang[i]);
            bug.cerciY[i] = bugy + bug_const.cercl * Math.sin(bug.angle + bug_const.cercang[i]);
        }*/
        /*
        // determine bug.antenna contact, bug.antenna contact angle, & cercus contact
        var xinc = 0;  // "touching" variables
        var yinc = 0;
        bug.antenna[0] = bug.antenna[1] = 0;
        for(int i=0; i<2; i++)
        {
            // check world edge contact
            if (bug.antennaX[i] <= ScaledMinx)
            {
                xinc += 1;
                if (!edget[i])
                {
                    bug.antenna[i] = true;
                    if (bug.angle > HALFPI && bug.angle <= PIANDAHALF) // more trig!!!
                        bug.antcang[i] = PI - bug.angle;
                    else if (bug.angle < PIANDAHALF)
                        bug.antcang[i] = bug.angle;
                    else
                        bug.antcang[i] = TWOPI - bug.angle;
                }
            }
            else if (bug.antennaX[i] >= ScaledMaxx)
            {
                xinc -= 1;
                if (!edget[i])
                {
                    bug.antenna[i] = true;
                    if (bug.angle <= PIANDAHALF && bug.angle >= HALFPI)
                        bug.antcang[i] = bug.angle - PI;
                    else if (bug.angle > PIANDAHALF)
                        bug.antcang[i] = TWOPI - bug.angle;
                    else
                        bug.antcang[i] = - bug.angle;
                }
            }
            if (bug.antennaY[i] <= ScaledMiny)
            {
                yinc += 1;
                if (!edget[i])
                {
                    bug.antenna[i] = true;
                    if (bug.angle <= PI)
                        bug.antcang[i] = bug.angle - HALFPI;
                    else
                        bug.antcang[i] = PIANDAHALF - bug.angle;
                }
            }
            else if (bug.antennaY[i] >= ScaledMaxy)
            {
                yinc -= 1;
                if (!edget[i])
                {
                    bug.antenna[i] = true;
                    if (bug.angle <= PI )
                        bug.antcang[i] = HALFPI - bug.angle;
                    else
                        bug.antcang[i] = bug.angle - PIANDAHALF;
                }
            }
            if (bug.cerciX[i] <= ScaledMinx)
                xinc += 1;
            else if (bug.cerciX[i] >= ScaledMaxx)
                xinc -= 1;
            if (bug.cerciY[i] <= ScaledMiny)
                yinc += 1;
            else if (bug.cerciY[i] >= ScaledMaxy)
                yinc -= 1;
            */
            /*
            // check box edge contact
            for (int j=0; j<environment->nblock; ++j)
            {
                // first check bug.antenna
                if (bugx < environment->blockx[j]
                && bug.antennaX[i] >= environment->blockx[j] - 1
                && bug.antennaY[i] >= environment->blocky[j]
                && bug.antennaY[i] <= environment->blocky[j] + BLOCKHEIGHT)
                {
                    xinc -= 1;
                    if (!edget[i])
                    {
                        bug.antenna[i] = true;
                        if (bug.angle <= PIANDAHALF && bug.angle >= HALFPI)
                            bug.antcang[i] = bug.angle - PI;
                        else if (bug.angle > PIANDAHALF)
                            bug.antcang[i] = TWOPI - bug.angle;
                        else
                            bug.antcang[i] = - bug.angle;
                    }
                }
                else if (bugx > environment->blockx[j] + BLOCKWIDTH
                && bug.antennaX[i] <= environment->blockx[j] + BLOCKWIDTH + 1
                && bug.antennaY[i] >= environment->blocky[j]
                && bug.antennaY[i] <= environment->blocky[j] + BLOCKHEIGHT)
                {
                    xinc += 1;
                    if (!edget[i])
                    {
                        bug.antenna[i] = true;
                        if (bug.angle > HALFPI && bug.angle <= PIANDAHALF)
                            bug.antcang[i] = PI - bug.angle;
                        else if (bug.angle < PIANDAHALF)
                            bug.antcang[i] = bug.angle;
                        else
                            bug.antcang[i] = TWOPI - bug.angle;
                    }
                }
                if (bugy < environment->blocky[j]
                && bug.antennaY[i] >= environment->blocky[j] - 2
                && bug.antennaX[i] >= environment->blockx[j]
                && bug.antennaX[i] <= environment->blockx[j] + BLOCKWIDTH)
                {
                    yinc -= 1;
                    if (!edget[i])
                    {
                        bug.antenna[i] = true;
                        if (bug.angle <= PI )
                            bug.antcang[i] = HALFPI - bug.angle;
                        else
                            bug.antcang[i] = bug.angle - PIANDAHALF;
                    }
                }
                else if (bugy > environment->blocky[j] + BLOCKHEIGHT
                && bug.antennaY[i] <= environment->blocky[j] + BLOCKHEIGHT + 2
                && bug.antennaX[i] >= environment->blockx[j]
                && bug.antennaX[i] <= environment->blockx[j] + BLOCKWIDTH)
                {
                    yinc += 1;
                    if (!edget[i])
                    {
                        bug.antenna[i] = true;
                        if (bug.angle <= PI)
                            bug.antcang[i] = bug.angle - HALFPI;
                        else
                            bug.antcang[i] = PIANDAHALF - bug.angle;
                    }
                }
                // now check cerci
                if (bugx < environment->blockx[j]
                && bug.cerciX[i] >= environment->blockx[j] - 1
                && bug.cerciY[i] >= environment->blocky[j]
                && bug.cerciY[i] <= environment->blocky[j] + BLOCKHEIGHT)
                    xinc -= 1;
                else if (bugx > environment->blockx[j] + BLOCKWIDTH
                && bug.cerciX[i] <= environment->blockx[j] + BLOCKWIDTH + 2
                && bug.cerciY[i] >= environment->blocky[j]
                && bug.cerciY[i] <= environment->blocky[j] + BLOCKHEIGHT)
                    xinc += 1;
                if (bugy < environment->blocky[j]
                && bug.cerciY[i] >= environment->blocky[j] - 2
                && bug.cerciX[i] >= environment->blockx[j]
                && bug.cerciX[i] <= environment->blockx[j] + BLOCKWIDTH)
                    yinc -= 1;
                else if (bugy > environment->blocky[j] + BLOCKHEIGHT
                && bug.cerciY[i] <= environment->blocky[j] + BLOCKHEIGHT + 2
                && bug.cerciX[i] >= environment->blockx[j]
                && bug.cerciX[i] <= environment->blockx[j] + BLOCKWIDTH)
                    yinc += 1;
            }
        }
        */
        /*
        if (xinc || yinc)  // if it bounced (it didn't if touch was on both sides)
        { // calculate bug position from old position + bounce
            bug.x += 20.5 * sgn(xinc) * bug_const.DT;  // (adjustable!) bounce
            bug.y += 20.5 * sgn(yinc) * bug_const.DT;
            for(int i=0; i<2; ++i) // recalculate bug.antenna & cercus tip positions
            {
                bug.antennaX[i] = bug.x + bug_const.antl * cos(bug.angle + bug_const.antang[i]);
                bug.antennaY[i] = bug.y + bug_const.antl * sin(bug.angle + bug_const.antang[i]);
                bug.cerciX[i] = bug.x + bug_const.cercl * cos(bug.angle + bug_const.cercang[i]);
                bug.cerciY[i] = bug.y + bug_const.cercl * sin(bug.angle + bug_const.cercang[i]);
            }
        }
        else
        {*/
            bug.x = bugx;
            bug.y = bugy;
        //}

        for (int i=0; i<6; ++i) // calculate leg angles & foot positions
        {
            if (bug.lastFoot[i] && bug.foot[i])
            { // foot stays down, stretch leg
                xa = bug.x + bug_const.attl[i] * cos(bug.angle + bug_const.attang[i]);
                ya = bug.y + bug_const.attl[i] * sin(bug.angle + bug_const.attang[i]);
                d = atan2(bug.footY[i] - ya,bug.footX[i] - xa);
                if (d < 0.)
                    d = TWOPI + d;
                bug.legang[i] = d - bug.angle;
                if (i < 3)
                {
                    while (bug.legang[i] > PI)
                        bug.legang[i] = bug.legang[i] - TWOPI;
                    while (bug.legang[i] <= -PI)
                        bug.legang[i] = TWOPI + bug.legang[i];
                }
                else
                {
                    while (bug.legang[i] < 0.)
                        bug.legang[i] = TWOPI + bug.legang[i];
                    while (bug.legang[i] >= TWOPI)
                        bug.legang[i] = bug.legang[i] - TWOPI;
                }
            }
            else
            { // move foot
                if (bug.lastFoot[i] && ((i >= 3 && bug.legang[i] < bug_const.maxlegang[i])
                || (i < 3 && bug.legang[i] > bug_const.maxlegang[i])))
                    bug.legang[i] = bug_const.maxlegang[i];
                if (i < 3)
                    bug.legang[i] += bug_const.DT * (leg[i].fF + leg[i].bF) * PI/15;
                else
                    bug.legang[i] -= bug_const.DT * (leg[i].fF + leg[i].bF) * PI/15;
                bug.footX[i]	= bug.x + bug_const.attl[i] * cos(bug.angle + bug_const.attang[i])
                                + bug_const.legl[i] * cos(bug.angle + bug.legang[i]);
                bug.footY[i]	= bug.y + bug_const.attl[i] * sin(bug.angle + bug_const.attang[i])
                                + bug_const.legl[i] * sin(bug.angle + bug.legang[i]);
            }
        }
        /*
        bug.energy -= ENERGYPERSECOND* bug_const.DT; // decrement bug's bug.energy
        if (bug.energy <= 0.)
        {
            bug.energy = 0;
            //bar(430,336,454,348);
            //outtextxy(430,336,"RIP");
            dead = true;
            return;
        }
        */
        /*
        bug.odor[0] = bug.odor[1] = bug.mouth_odor = 0.;
        bug.mouthX = bug.x + bug_const.hdtl * cos(bug.angle + bug_const.hdtang);
        bug.mouthY = bug.y + bug_const.hdtl * sin(bug.angle + bug_const.hdtang);
        cf = 0;
        mo = 0.;
        for(int i=0; i<environment->nfood; ++i)
        { // calculate odors for each bug.antenna & mouth
            for(int j=0; j<2; ++j)
            {
                d = bug.antennaX[j] - environment->foodx[i];
                f = bug.antennaY[j] - environment->foody[i];
                bug.odor[j] += .75 * environment->foodsize[i]/(d*d + f*f); // (adjustable!)
            }
            d = bug.mouthX - environment->foodx[i];
            f = bug.mouthY - environment->foody[i];
            d = d*d + f*f;
            bug.mouth_odor += environment->foodsize[i]/d;
            mouthd[i] = sqrt(d);
            if (bug.mouth_odor > mo)
            { // save largest bug.mouth_odor
                mo = bug.mouth_odor;
                cf = i;
            }
        }
        */
        /*
        if (bug.last_mouth && !bug.mouth)  // mouth was open, now closed
        {
            bug.energy += BITEENERGY;
            environment->foodsize[cf] -= BITEENERGY;
            environment->foodsize[cf] = max(environment->foodsize[cf], 0);
            environment->foodr[cf] = sqrt(environment->foodsize[cf]/PI);
        }
        // check for mouth contact
        bug.mouth_contact = false;
        for(int i=0; i<environment->nfood; ++i)
        {
            if (mouthd[i] > 2*environment->foodr[i])   // change from original
                continue;
            bug.mouth_contact = true;
            break;
        }*/
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
                    value = message.payload[key];
                    if(key.in_list($scope.outputs))
                        $scope.update_output(key, value)
                    else
                        $scope[key] = value; // for updating {{ }} variables, but we should do this more intelligently
                }
                //$scope.bug.angle += 0.1; // demo spin the bug!
                $scope.calculate_state();
                $scope.render_state();
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