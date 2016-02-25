/**
 * Created by gbiddison on 7/10/15.
 */
SCALE = 1.0;

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
        //radians = -(radians + Math.PI/2.0); // to get counter-clockwise rotation, orientated 0.0 = right facing
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
        var bug_const = $scope.bug_const;
        var x = bug.x + ctx.canvas.width/2.;
        var y = bug.y + ctx.canvas.height/2.;
        //console.log("rx: (" + x + ", " + y + ")");
        var scale = SCALE;

        var leg_points = bug.leg_points;    // we draw from "leg" to "foot"
        var foot_points = bug.foot_points;
        for(var i=0; i<6; ++i){
            foot_points[i] = [leg_points[i][0] + bug_const.legl[i] * Math.cos(bug.legang[i]),
                              leg_points[i][1] + bug_const.legl[i] * Math.sin(bug.legang[i])];
        }

        //draw head
        $scope.draw_poly(ctx, $scope.transform(bug.head_points, x, y, bug.angle, scale));
        //if (bug.mouth)
        //    dc.DrawLine( bugp.head[0],bugp.head[1],bugp.head[4],bugp.head[5]);

        // draw body
        $scope.draw_poly(ctx, $scope.transform(bug.body_points, x, y, bug.angle, scale));

        // draw antennae
        $scope.draw_lines(ctx, $scope.transform(bug.antb_points, x, y, bug.angle, scale),
                               $scope.transform(bug.ant_points, x, y, bug.angle, scale));
        // draw cerci
        $scope.draw_lines(ctx, $scope.transform(bug.cerb_points, x, y, bug.angle, scale),
                               $scope.transform(bug.cer_points, x, y, bug.angle, scale));

        // draw legs & feet
        $scope.draw_lines(ctx, $scope.transform(bug.leg_points, x, y, bug.angle, scale),
                               $scope.transform(bug.foot_points, x, y, bug.angle, scale));
        // draw foot down pad
        for(var n in bug.foot){
            if (bug.foot[n]){
                var i = bug.leg_index.indexOf(n);
                var fpt = $scope.transform(bug.foot_points, x, y, bug.angle, scale);
                var w = 2. * scale;
                var pad = [[fpt[i][0]-w, fpt[i][1]-w], [fpt[i][0]+w, fpt[i][1]-w],
                           [fpt[i][0]+w, fpt[i][1]+w], [fpt[i][0]-w, fpt[i][1]+w]];
                $scope.draw_poly(ctx, pad);
            }
        }
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

	        'maxlegang': [Math.PI/5, Math.PI/12, Math.PI/12, Math.PI - Math.PI/5, Math.PI - Math.PI/12, Math.PI - Math.PI/12],
            'minlegang': [0., -Math.PI/12, -Math.PI/8, Math.PI, Math.PI + Math.PI/12, Math.PI + Math.PI/8],

            // ANTENNA consts
            'antbl':    Math.sqrt(6.0*6 + 26*26),                      // distance from origin
            'antbang':  [Math.atan2(26.0,6), Math.atan2(26.0,-6)],     // angle from origin
        	'antl':     Math.sqrt(30.0*30 + 65*65),                    // length
        	'antang':   [Math.atan2(65.0,30), Math.atan2(65.0,-30)],   // angle

            // CERCI consts
            'cerbl':    Math.sqrt(2.0*2 + 30*30),
            'cerbang':  [Math.atan2(-30.0,2), Math.atan2(-30.0,-2)],
            'cercl':    Math.sqrt(34.0*34 + 8*8),
            'cercang':  [Math.atan2(-34.0,8), Math.atan2(-34.0,-8)],
        }

        var bug = {   // state
            'x': 0.0,
            'y': 0.0,
            'angle': -Math.PI/2, // NOT zero is straight right, pi is straight left, counter-clockwise rotations
            'legang':   [0., 0., 0., Math.PI, Math.PI, Math.PI],
            'mouth': false,
            'last_mouth': false,
            'leg_index': ['L1', 'L2', 'L3', 'R1', 'R2', 'R3'],
            'leg': { 'L1': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'L2': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'L3': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'R1': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'R2': {'backward_force':0., 'forward_force':0., 'lateral_force':0.},
                     'R3': {'backward_force':0., 'forward_force':0., 'lateral_force':0.}
                   },
            'foot': {'L1':true, 'L2':true, 'L3':true, 'R1':true, 'R2':true, 'R3':true},
            'last_foot': {'L1':true, 'L2':true, 'L3':true, 'R1':true, 'R2':true, 'R3':true},
            'antenna_contact': [false, false],   // antenna touching something
            'antenna_contact_angle': [0.0, 0.0], // angle antenna makes with contact, only valid if contact = true
            'last_edge_contact_angle': [0.0, 0.0],
            'antenna_edge_time': [0, 0],     // counter since last edge contact
            'head_points': [[0,0], [0,0], [0,0], [0,0]],
            'body_points': [[0,0], [0,0], [0,0], [0,0], [0,0]],
            'leg_points':  [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0]],  // leg attachment to body
            'foot_points': [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0]],  // free end of leg
            'antb_points': [[0,0], [0,0]], // antenna attachment to body
            'ant_points': [[0,0], [0,0]],  // free tip of antenna
            'cerb_points': [[0,0], [0,0]], // cerci attachment to body
            'cer_points': [[0,0], [0,0]],  // free tip of cerci

        };
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

        var antb_points = bug.antb_points;  // we draw from antb to ant
        var ant_points = bug.ant_points;
        var cerb_points = bug.cerb_points;
        var cer_points = bug.cer_points;
        for(var i=0; i<2; ++i){
            antb_points[i] = [bug_const.antbl * Math.cos(bug_const.antbang[i]),
                              bug_const.antbl * Math.sin(bug_const.antbang[i])];
            ant_points[i] = [bug_const.antl * Math.cos(bug_const.antang[i]),
                              bug_const.antl * Math.sin(bug_const.antang[i])];
            cerb_points[i] = [bug_const.cerbl * Math.cos(bug_const.cerbang[i]),
                              bug_const.cerbl * Math.sin(bug_const.cerbang[i])];
            cer_points[i] = [bug_const.cercl * Math.cos(bug_const.cercang[i]),
                              bug_const.cercl * Math.sin(bug_const.cercang[i])];
        }

	    $scope.bug = bug;
	    $scope.bug_const = bug_const;
        $scope.render_state();
    };

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

        if( node == 'FOOTL2')
            console.log("update: " + node + " " + value);
        if( node.in_list(mouth)){
            bug.last_mouth = bug.mouth;
            bug.mouth = value > 0.5;
        }else if( node.in_list(foot)){
            var foot_index = node.slice(-2); // eg "L1"
            bug.foot[foot_index] = value > 0;
            // console.log("updated foot: " + node + " " + foot_index + " " + value + " " + bug.foot[foot_index])
        }else{
            var leg_index = node.slice(-2); // eg "L1"
            if( node.in_list(backward))     bug.leg[leg_index].backward_force = 50. * value;  // 50 original
            else if( node.in_list(forward)) bug.leg[leg_index].forward_force = 50. * value;   // 50 original
            else if( node.in_list(lateral)) bug.leg[leg_index].lateral_force = 7. * value;
        }
    };

    $scope.calculate_state = function() {
        var ctx = document.getElementById("c").getContext("2d");
        var scale = SCALE;
        var maxx = ctx.canvas.width / 2., maxy = ctx.canvas.height / 2.;
        var minx = -maxx, miny = -maxy;
        var bug_const = $scope.bug_const;
        var bug = $scope.bug;
        var leg = bug.leg; // alias for brevity
        // seems to work best with this fixed,
        // gui framerate is a bit hicuppy
        var TIMECONSTANT = 1 / 200.0; // seconds per simulated time step -- neuron time constant is 1/1000, would make sense if they were the same
        var DT = TIMECONSTANT;
        var PI = Math.PI;
        var TWOPI = 2.0*PI;
        var PIANDAHALF = 1.5*PI;
        var HALFPI = 0.5*PI;
        var oldx = bug.x;
        var oldy = bug.y;

        // calculate bug's translational velocity
        var d = 0.;
        for(var i in bug.foot) // sum forces of legs that are down
            d += bug.foot[i] * (leg[i].backward_force - leg[i].forward_force);
        d = d/2.; //(adjustable!) originally d/2.0

        // calculate bug's angular velocity
        var f = bug.foot['L1'] * leg['L1'].lateral_force - bug.foot['R1'] * leg['R1'].lateral_force;
        f = f/6.; // (adjustable!) (5 to 6)  original f/6

        var bugx = bug.x - Math.sin(bug.angle) * d * DT;
        var bugy = bug.y + Math.cos(bug.angle) * d * DT;

        // calc sideways force du
        var s = bug.foot['L2'] * leg['L2'].lateral_force - bug.foot['R2'] * leg['R2'].lateral_force;
        s = 2. * s;  // (adjustable!) (20 to 2)

        bugx -= Math.cos(bug.angle) * s * DT;
        bugy -= Math.sin(bug.angle) * s * DT;
        bug.angle += f * DT;

        if (bug.angle < 0)                 // trig!!!
            bug.angle = TWOPI + bug.angle;
        if (bug.angle >= TWOPI)
            bug.angle = bug.angle - TWOPI;

        //console.log("d: " + d + " f:" + f + " s:" + s);

        // determine antenna contact, antenna contact angle & cercis contact based on new coords
        //
        var xinc = 0, yinc = 0;  // "touching" variables
        var ant_pts = $scope.transform(bug.ant_points, bugx, bugy, bug.angle, 1.0);
        var cer_pts = $scope.transform(bug.cer_points, bugx, bugy, bug.angle, 1.0);

        var edge_time = bug.antenna_edge_time;
        var antenna_contact = bug.antenna_contact;
        var contact_angle = bug.antenna_contact_angle;
        for(var i=0; i<2; i++){
            // check world edge contact
            if(ant_pts[i][0] <= minx){
                console.log("x-" + i + " " + ant_pts[i][0] + " <= " + minx )

                xinc += 1;
                if (!edge_time[i]){
                    antenna_contact[i] = true;
                    if (bug.angle > HALFPI && bug.angle <= PIANDAHALF) contact_angle[i] = PI - bug.angle;
                    else if (bug.angle < PIANDAHALF)                   contact_angle[i] = bug.angle;
                    else                                               contact_angle[i] = TWOPI - bug.angle;
                }
            }
            else if(ant_pts[i][0] >= maxx){
                console.log("x-" + i + " " + ant_pts[i][0] + " >= " + maxx )

                xinc -= 1;
                if (!edge_time[i]){
                    antenna_contact[i] = true;
                    if (bug.angle <= PIANDAHALF && bug.angle >= HALFPI) contact_angle[i] = bug.angle - PI;
                    else if (bug.angle > PIANDAHALF)                    contact_angle[i] = TWOPI - bug.angle;
                    else                                                contact_angle[i] = - bug.angle;
                }
            }
            if(ant_pts[i][1] <= miny){
                console.log("y-" + i + " " + ant_pts[i][1] + " <= " + miny )

                yinc += 1;
                if (!edge_time[i]){
                    antenna_contact[i] = true;
                    if (bug.angle <= PI) contact_angle[i] = bug.angle - HALFPI;
                    else                 contact_angle[i] = PIANDAHALF - bug.angle;
                }
            }
            else if(ant_pts[i][1] >= maxy){
                console.log("y-" + i + " " + ant_pts[i][0] + " <= " + minx )

                yinc -= 1;
                if (!edge_time[i]){
                    antenna_contact[i] = true;
                    if (bug.angle <= PI ) contact_angle[i] = HALFPI - bug.angle;
                    else                  contact_angle[i] = bug.angle - PIANDAHALF;
                }
            }

            // check cercus for fun

            if (cer_pts[i][0] <= minx)      xinc += 1;
            else if (cer_pts[i][0] >= maxx) xinc -= 1;
            if (cer_pts[i][1] <= miny)      yinc += 1;
            else if (cer_pts[i][1] >= maxy) yinc -= 1;


/*
            // check box edge contact
            for (int j=0; j<environment->nblock; ++j){
                // first check bug.antenna
                if (bugx < environment->blockx[j]
                && bug.antennaX[i] >= environment->blockx[j] - 1
                && bug.antennaY[i] >= environment->blocky[j]
                && bug.antennaY[i] <= environment->blocky[j] + BLOCKHEIGHT){
                    xinc -= 1;
                    if (!edget[i]){
                        bug.antenna[i] = true;
                        if (bug.angle <= PIANDAHALF && bug.angle >= HALFPI) bug.antcang[i] = bug.angle - PI;
                        else if (bug.angle > PIANDAHALF)                    bug.antcang[i] = TWOPI - bug.angle;
                        else                                                bug.antcang[i] = - bug.angle;
                    }
                }else if (bugx > environment->blockx[j] + BLOCKWIDTH
                && bug.antennaX[i] <= environment->blockx[j] + BLOCKWIDTH + 1
                && bug.antennaY[i] >= environment->blocky[j]
                && bug.antennaY[i] <= environment->blocky[j] + BLOCKHEIGHT){
                    xinc += 1;
                    if (!edget[i]){
                        bug.antenna[i] = true;
                        if (bug.angle > HALFPI && bug.angle <= PIANDAHALF) bug.antcang[i] = PI - bug.angle;
                        else if (bug.angle < PIANDAHALF)                   bug.antcang[i] = bug.angle;
                        else                                               bug.antcang[i] = TWOPI - bug.angle;
                    }
                }
                if (bugy < environment->blocky[j]
                && bug.antennaY[i] >= environment->blocky[j] - 2
                && bug.antennaX[i] >= environment->blockx[j]
                && bug.antennaX[i] <= environment->blockx[j] + BLOCKWIDTH){
                    yinc -= 1;
                    if (!edget[i]){
                        bug.antenna[i] = true;
                        if (bug.angle <= PI ) bug.antcang[i] = HALFPI - bug.angle;
                        else                  bug.antcang[i] = bug.angle - PIANDAHALF;
                    }
                }
                else if (bugy > environment->blocky[j] + BLOCKHEIGHT
                && bug.antennaY[i] <= environment->blocky[j] + BLOCKHEIGHT + 2
                && bug.antennaX[i] >= environment->blockx[j]
                && bug.antennaX[i] <= environment->blockx[j] + BLOCKWIDTH){
                    yinc += 1;
                    if (!edget[i]){
                        bug.antenna[i] = true;
                        if (bug.angle <= PI) bug.antcang[i] = bug.angle - HALFPI;
                        else                 bug.antcang[i] = PIANDAHALF - bug.angle;
                    }
                }
                // now check cerci
                if (bugx < environment->blockx[j]
                && bug.cerciX[i] >= environment->blockx[j] - 1
                && bug.cerciY[i] >= environment->blocky[j]
                && bug.cerciY[i] <= environment->blocky[j] + BLOCKHEIGHT) xinc -= 1;
                else if (bugx > environment->blockx[j] + BLOCKWIDTH
                && bug.cerciX[i] <= environment->blockx[j] + BLOCKWIDTH + 2
                && bug.cerciY[i] >= environment->blocky[j]
                && bug.cerciY[i] <= environment->blocky[j] + BLOCKHEIGHT) xinc += 1;
                if (bugy < environment->blocky[j]
                && bug.cerciY[i] >= environment->blocky[j] - 2
                && bug.cerciX[i] >= environment->blockx[j]
                && bug.cerciX[i] <= environment->blockx[j] + BLOCKWIDTH) yinc -= 1;
                else if (bugy > environment->blocky[j] + BLOCKHEIGHT
                && bug.cerciY[i] <= environment->blocky[j] + BLOCKHEIGHT + 2
                && bug.cerciX[i] >= environment->blockx[j]
                && bug.cerciX[i] <= environment->blockx[j] + BLOCKWIDTH) yinc += 1;
            }
*/
        }


        if (xinc || yinc){
            // if it bounced (it didn't if touch was on both sides)
            // calculate bug position from old position + bounce, ignore forces
            bug.x += 20.5 * Math.sign(xinc) * DT;  // (adjustable!) bounce
            bug.y += 20.5 * Math.sign(yinc) * DT;
        }else{
            // or use the force-determined position if it didn't bounce
            bug.x = bugx;
            bug.y = bugy;
            //console.log("b: (" + bug.x + ", " + bug.y + ")");
        }

        for(var i in bug.leg_index) // calculate leg angles & foot positions
        {
            var n = bug.leg_index[i];
            if(bug.last_foot[n] && bug.foot[n])
            { // foot stays down, slides along ground

                var fpt = $scope.transform(bug.foot_points, oldx, oldy, bug.angle, 1.0);
                var lgt = $scope.transform(bug.leg_points, bug.x, bug.y, bug.angle, 1.0);

                var d = Math.atan2(fpt[i][1] - lgt[i][1], fpt[i][0] - lgt[i][0]);
                if (d < 0.)
                    d = TWOPI + d;
                bug.legang[i] = d - bug.angle;

                if (i < 3)
                {
                    while(bug.legang[i] > PI)   bug.legang[i] -= TWOPI;
                    while(bug.legang[i] <= -PI) bug.legang[i] += TWOPI;
                }
                else
                {
                    while(bug.legang[i] < 0.)     bug.legang[i] += TWOPI;
                    while(bug.legang[i] >= TWOPI) bug.legang[i] -= TWOPI;
                }
                //console.log("'" + n + "'[" + i + "]: " + bug.legang[i] );
            }
            else
            { // foot is up, move leg rather than force body
                if (bug.last_foot[n] && ((i >= 3 && bug.legang[i] < bug_const.maxlegang[i])
                || (i < 3 && bug.legang[i] > bug_const.maxlegang[i])))
                    bug.legang[i] = bug_const.maxlegang[i];
                if (i < 3)
                    bug.legang[i] += DT * (leg[n].forward_force + leg[n].backward_force) * PI/15;
                else
                    bug.legang[i] -= DT * (leg[n].forward_force + leg[n].backward_force) * PI/15;
                //console.log("*'" + n + "'[" + i + "]: " + bug.legang[i] );
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

        for(var i in leg)
        {
            bug.last_foot[i] = bug.foot[i]; // save foot states
            leg[i].backward_force = leg[i].forward_force = leg[i].lateral_force = 0; // clear forces
        }
    }

    $scope.send_sensors = function()
    {
        var bug = $scope.bug;
        var bug_const = $scope.bug_const;
        var LegAngleForward	= ['FASL1', 'FASL2', 'FASL3',
                               'FASR1', 'FASR2', 'FASR3'];
        var LegAngleBackward = ['BASL1', 'BASL2', 'BASL3',
                                'BASR1', 'BASR2', 'BASR3'];
        var AntennaContact   = ['ATSL', 'ATSR'];
        var OdorStrength     = ['ACSL', 'ACSR', 'MCS'];
        var EnergyCapacity   = ['ES'];
        var MouthContact     = ['MTS'];

        /* Parameters -- originally these were part of the network, but these are really state parameters, not network parameters
        // FAS, BAS: neuron[5].paramsSensorCurrent[0] 1e-008
        // ATS neuron[45].paramsSensorCurrent[0] 5.09e-009
        // ATS neuron[45].paramsSensorCurrent[1] 0.02
        // ACS neuron[61].paramsSensorCurrent[0] 1e-010
        // ACS neuron[61].paramsSensorCurrent[1] 2.5e-012
        // ES neuron[63].paramsSensorCurrent[0] 5e-012
        // MTS neuron[68].paramsSensorCurrent[0] 5e-009
        // MCS neuron[69].paramsSensorCurrent[0] 5e-011
        // MCS neuron[69].paramsSensorCurrent[1] 5e-011
        */
        // LCS is an 'input' neuron, but it self stimulating, a beat generator

        var sensors = {}
        for(var n in $scope.inputs)
        {
            var node = $scope.inputs[n];
            var value = 0;
            if( node.in_list(LegAngleForward)){
                var leg_index = node.slice(-2); // eg "L1"
                var i = bug.leg_index.indexOf(leg_index);
                if(i < 3){ // left
                    if (bug.legang[i] >= bug_const.maxlegang[i]) value = 1e-008;
                    //console.log("'" + node + "'[" + i + "]: " + value);
                }else{ // right
                    if (bug.legang[i] <= bug_const.maxlegang[i]) value = 1e-008;
                    //console.log("'" + node + "'[" + i + "]: " + value);
                }
            }else if(node.in_list(LegAngleBackward)){
                var leg_index = node.slice(-2); // eg "L1"
                var i = bug.leg_index.indexOf(leg_index);
                if(i < 3){ // left
                    if (bug.legang[i] <= bug_const.minlegang[i]) value = 1e-008;
                    //console.log("'" + node + "'[" + i + "]: " + value);
                }else{
                    if (bug.legang[i] >= bug_const.minlegang[i]) value = 1e-008;
                    //console.log("'" + node + "'[" + i + "]: " + value);
                }
            }else if(node.in_list(AntennaContact)){
                var antenna_index = node.slice(-1) // eh "L" or "R"
                var i = antenna_index == "L" ? 0 : 1;
                if (!bug.antenna_edge_time[i]){
                    if (bug.antenna_contact[i]){
                        bug.antenna_edge_time[i] = 100;
                        bug.last_edge_contact_angle[i] = bug.antenna_contact_angle[i];
                        value = 5.09e-009 * bug.last_edge_contact_angle[i];
                    }else I = 0;
                }else{
                    bug.antenna_edge_time[i]--;
                    value = 5.09e-009 * bug.last_edge_contact_angle[i];
                }
            }else if(node.in_list(OdorStrength)){
                var antenna_index = node.slice(-1) // eh "L" or "R" or "S" for mouth
                var i = antenna_index == "L" ? 0 : antenna_index == "R" ? 1 : 2;
                if (i < 2) value = 1e-010 * (i==0? 0.0 : 0.0)/*bug.antenna_odor[j]*/ - 2.5e-012;
                else       value = 5e-011 * 0.0/*bug.mouth_odor*/ - 5e-011;
            }
            sensors[node] = value;
        }
/*

                case Neuron::OdorStrength: // bug.odor strength
                    if (j < 2)
                        I = *pI * bug.odor[j] - *(pI+1);
                    else
                        I = *pI * bug.mouth_odor - *(pI+1);
                    break;

                    case Neuron::EnergyCapacity: // bug.energy capacity
                        I = *pI * bug.energy;
                    break;

                    case Neuron::MouthContact: // mouth contact
                        if (bug.mouth_contact)
                            I = *pI;
                        else
                            I = 0;
                    break;

                    default:
                        I = 0;
                break;
            }

            return(I);
        }
*/
        //console.log(sensors);

        WebSocketService.command('sensors', sensors);
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
                $scope.send_sensors();
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