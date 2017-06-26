{
    init: function(elevators, floors) {
        global_pickup_reqs = {'global': []};

        elevators.forEach(function(E) {
            E.dest_reqs = {};
            E._global = global_pickup_reqs;

            // register destinations
            E.on("floor_button_pressed", function(floornum) {
                E.dest_reqs[floornum] += 1;
            });

            // register unloads
            E.on("stopped_at_floor", function(floornum) {
                // whoever was coming to this floor should get out
                delete E.dest_reqs[floornum];
            });

            // service requests
            E.on("idle", function() {
                // service by closest destination
                var f = E.currentFloor();
                //var reqs = Object.keys(E.dest_reqs).sort(function(a, b) {
                    //return Math.abs(a - f) < Math.abs(b - f) ? a : b;
                //});
                var reqs = Object.keys(E.dest_reqs).sort(function(a, b) {
                    return a < b ? a : b;
                });
                reqs.forEach(function(req) {
                    E.goToFloor(req);
                });
            });

            E.setDir = function(dir) {
                if (dir === "up") {
                    E.goingUpIndicator(true);
                    E.goingDownIndicator(false);
                }
                if (dir === "down") {
                    E.goingUpIndicator(false);
                    E.goingDownIndicator(true);
                }
                if (dir === "stopped") {
                    E.goingUpIndicator(false);
                    E.goingDownIndicator(false);
                }
            };
        });

        // register requests for pickup
        floors.forEach(function(floor) {
            floor.on("up_button_pressed", function() {
                var key = {'src': floor.floorNum(), 'dir': 'up'};
                global_pickup_reqs['global'].push(key);
            });
            floor.on("down_button_pressed", function() {
                var key = {'src': floor.floorNum(), 'dir': 'down'};
                global_pickup_reqs['global'].push(key);
            });
        });
    },

    update: function(dt, elevators, floors) {
        // set elevator indicators
        elevators.forEach(function(E) {
            if (E.destinationQueue.length > 0) {
                var next = E.destinationQueue[0];
                E.setDir((E.currentFloor() < next) ? "up" : "down");
            }
            if (E.currentFloor() === 0) {
                E.setDir("up");
            }
        });

        // schedule each pickup request to an elevator
        var global_reqs = elevators[0]._global;
        var keep = [];
        global_reqs['global'].forEach(function(req) {  // req: {src, dir}
            // elevators not fully loaded
            // elevators in closest floor
            // elevators with smallest queue
            // going the same way ... can't know if it going to keep doing so

            var elevs = elevators.filter(function(E) {
                return E.loadFactor() < 0.05;
            });

            if (elevs.length < 1) {
                keep.push(req);
            } else {
                // pick smallest queue
                elevs.reduce(function(a, b) {
                    return (a.destinationQueue.length <
                            b.destinationQueue.length ? a : b);
                }).goToFloor(req['src']);
            }
        });
        // clear all assigned reqs from global queue
        global_reqs['global'] = keep;
    }
}
