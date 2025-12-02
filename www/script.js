// This script appears to be for a particle animation, possibly for the 'Oval' or a background effect.
// Its integration with the current SiriWave/IronMan setup needs to be carefully managed
// to ensure it doesn't conflict or appear when not intended.
// Based on the provided index.html, this script is linked but its output on "canvasOne"
// is not explicitly controlled by the show/hide logic implemented in controller.js
// for SiriWave or Iron Man.

window.addEventListener("load", windowLoadHandler, false);

// Particle sphere properties
var sphereRad = 140; // Radius of the sphere on which particles are initially placed
var radius_sp = 1; // Unused variable, potentially for future feature
var r = 0, g = 255, b = 255; // RGB color for particles (cyan)

function windowLoadHandler() {
    // Calls the main canvas application function when the window finishes loading
    canvasApp();
}

function canvasSupport() {
    // Checks if the browser supports HTML5 Canvas using Modernizr
    return Modernizr.canvas;
}

function canvasApp() {
    // If canvas is not supported, exit the function
    if (!canvasSupport()) return;

    // Get the canvas element and its 2D rendering context
    var theCanvas = document.getElementById("canvasOne");
    var context = theCanvas.getContext("2d");

    // Get the display dimensions of the canvas
    var displayWidth = theCanvas.width;
    var displayHeight = theCanvas.height;

    // 3D projection parameters
    var fLen = 320; // Focal length of the camera
    var projCenterX = displayWidth / 2; // Projection center X
    var projCenterY = displayHeight / 2; // Projection center Y
    var zMax = fLen - 100; // Maximum Z-depth for particle rendering
    var particleAlpha = 1; // Alpha (opacity) of particles
    var turnSpeed = 2 * Math.PI / 1200; // Speed of sphere rotation

    // Sphere center in 3D space
    var sphereCenterX = 0;
    var sphereCenterY = 0;
    var sphereCenterZ = -3 - sphereRad; // Placed behind the camera

    var particleRad = 2; // Radius of individual particles
    var zeroAlphaDepth = -150; // Z-depth at which particle alpha becomes 0
    var gravity = 0; // Unused variable, potentially for gravity effect
    var rgbString = "rgba(" + r + "," + g + "," + b + ","; // Base RGB string for particle color

    var count = 0; // Current number of active particles
    var numToAddEachFrame = 4; // Number of new particles to add per frame
    
    // Linked lists for managing particles
    var particleList = {}; // Active particles
    var recycleBin = {}; // Recycled (inactive) particles

    // Start the animation timer
    var timer = setInterval(onTimer, 1000 / 24); // 24 frames per second

    function onTimer() {
        // Add new particles if count is below 1000
        if (count < 1000) {
            for (let i = 0; i < numToAddEachFrame; i++) {
                addParticle();
            }
        }

        // Clear the canvas for the new frame
        context.clearRect(0, 0, displayWidth, displayHeight);

        // Iterate through active particles
        var p = particleList.first;
        while (p != null) {
            // Store the next particle before potential removal
            var nextParticle = p.next;

            // Rotate the particle's position
            p.x += p.velX;
            p.y += p.velY;
            p.z += p.velZ;

            var rString = rgbString;
            var alpha = particleAlpha;
            var zPos = p.z;

            // Adjust alpha based on Z-position for depth fading
            if (zPos > -fLen) {
                var oneMinus = 1 - zPos / displayWidth;
                alpha = alpha * (oneMinus);
                context.fillStyle = rString + alpha + ")";
            } else {
                // Recycle particle if it goes too far back
                recycle(p);
                p = nextParticle;
                continue;
            }

            // Project 3D coordinates to 2D screen coordinates
            var scale = fLen / (fLen + zPos);
            var x = projCenterX + p.x * scale;
            var y = projCenterY + p.y * scale;
            var rad = particleRad * scale;

            // Draw the particle
            context.beginPath();
            context.arc(x, y, rad, 0, 2 * Math.PI, false);
            context.closePath();
            context.fill();

            p = nextParticle; // Move to the next particle
        }
    }

    function addParticle() {
        var p = null;
        // Try to get a particle from the recycle bin
        if (recycleBin.first != null) {
            p = recycleBin.first;
            recycleBin.remove(p);
        } else {
            // If recycle bin is empty, create a new particle
            p = new Particle();
        }

        count++; // Increment active particle count

        // Add the new particle to the active particle list
        if (particleList.first == null) {
            particleList.first = p;
            p.prev = null;
            p.next = null;
        } else {
            p.next = particleList.first;
            particleList.first.prev = p;
            particleList.first = p;
            p.prev = null;
        }

        // Randomly place particle on the surface of a sphere
        var theta = Math.random() * Math.PI; // Latitude
        var phi = Math.random() * 2 * Math.PI; // Longitude

        p.x = sphereCenterX + sphereRad * Math.sin(theta) * Math.sin(phi);
        p.y = sphereCenterY + sphereRad * Math.cos(theta);
        p.z = sphereCenterZ + sphereRad * Math.sin(theta) * Math.cos(phi);

        p.velX = 0; // No initial velocity
        p.velY = 0;
        p.velZ = 0;
    }

    function recycle(p) {
        // Recycle a particle
        count--; // Decrement active particle count
        particleList.remove(p); // Remove from active list
        
        // Add to recycle bin
        p.next = recycleBin.first;
        recycleBin.first = p;
    }

    // Linked list method for removing a particle
    function remove(p) {
        if (this.first == p) {
            if (p.next != null) {
                p.next.prev = null;
                this.first = p.next;
            } else {
                this.first = null;
            }
        } else {
            if (p.next == null) {
                p.prev.next = null;
            } else {
                p.prev.next = p.next;
                p.next.prev = p.prev;
            }
        }
    }

    // Particle object constructor
    function Particle() {
        this.x = this.y = this.z = 0; // Position
        this.velX = this.velY = this.velZ = 0; // Velocity
        this.next = this.prev = null; // Pointers for linked list
    }

    // Add the remove method to the prototype of linked lists (particleList and recycleBin)
    particleList.remove = remove;
    recycleBin.remove = remove;
}
