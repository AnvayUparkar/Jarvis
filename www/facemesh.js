/**
 * facemesh.js
 * 
 * Implements real-time FaceMesh detection using TensorFlow.js and MediaPipe.
 * Includes emotion detection based on facial landmark analysis.
 */

let video, canvas, ctx;
let model;
let rafID;
let isRunning = false;

// Configuration
const VIDEO_WIDTH = 640;
const VIDEO_HEIGHT = 480;
const FACE_MESH_CONFIDENCE = 0.9;
const MAX_FACES = 1;

// Current detected emotion
let currentEmotion = 'neutral';

// Landmark indices for emotion detection (MediaPipe FaceMesh)
const LANDMARK_INDICES = {
    // Lips
    UPPER_LIP_TOP: 13,
    LOWER_LIP_BOTTOM: 14,
    LEFT_LIP_CORNER: 61,
    RIGHT_LIP_CORNER: 291,
    UPPER_LIP_CENTER: 0,

    // Eyebrows
    LEFT_EYEBROW_INNER: 107,
    LEFT_EYEBROW_OUTER: 70,
    RIGHT_EYEBROW_INNER: 336,
    RIGHT_EYEBROW_OUTER: 300,

    // Eyes
    LEFT_EYE_TOP: 159,
    LEFT_EYE_BOTTOM: 145,
    RIGHT_EYE_TOP: 386,
    RIGHT_EYE_BOTTOM: 374,

    // Nose
    NOSE_TIP: 1,

    // Face contour reference points
    CHIN: 152,
    FOREHEAD_CENTER: 10
};

// Emoji mappings
const EMOTION_EMOJIS = {
    happy: '😊',
    sad: '😢',
    surprised: '😮',
    neutral: '😐',
    angry: '😠',
    tensed: '😬'
};

/**
 * Initializes the FaceMesh system.
 */
async function startFaceMesh() {
    if (isRunning) return;

    try {
        await setupCamera();
        await loadFaceMeshModel();

        isRunning = true;
        renderPrediction();

        console.log("FaceMesh System Started");
        updateEmotionDisplay('neutral');
    } catch (error) {
        console.error("Failed to start FaceMesh:", error);
        alert("Error starting FaceMesh: " + error.message);
    }
}

/**
 * Stops the FaceMesh system.
 */
// --- EMOTION TRANSMISSION VIA FLASK ---
let lastSentEmotion = null;
let lastSentTime = 0;
const EMOTION_THROTTLE_MS = 200; // Throttle to 200ms for faster updates

function sendEmotionToBackend(emotion) {
    const now = Date.now();

    // Simple debounce for SAME emotion (prevent spam but allow fast repeats)
    if (emotion === lastSentEmotion && (now - lastSentTime < 500)) return;
    if (now - lastSentTime < EMOTION_THROTTLE_MS) return;

    // Send via POST
    fetch("http://localhost:5013/emotion", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            emotion: emotion,
            timestamp: now
        })
    }).catch(err => {
        // Silently fail or log sparingly to avoid console spam if server is down
        // console.warn("Emotion send failed:", err);
    });

    lastSentEmotion = emotion;
    lastSentTime = now;
}

// Ensure stop logic is clean
function stopFaceMesh() {
    isRunning = false;
    if (rafID) {
        cancelAnimationFrame(rafID);
    }

    if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }

    if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    updateEmotionDisplay('neutral');
    console.log("FaceMesh System Stopped");
}

/**
 * Sets up the webcam.
 */
async function setupCamera() {
    video = document.getElementById('video-input');

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Browser API navigator.mediaDevices.getUserMedia not available');
    }

    const stream = await navigator.mediaDevices.getUserMedia({
        'audio': false,
        'video': {
            facingMode: 'user',
            width: VIDEO_WIDTH,
            height: VIDEO_HEIGHT
        },
    });

    video.srcObject = stream;

    return new Promise((resolve) => {
        video.onloadedmetadata = () => {
            resolve(video);
        };
    });
}

/**
 * Loads the FaceMesh model.
 */
async function loadFaceMeshModel() {
    console.log("Loading FaceMesh Model...");

    model = await faceLandmarksDetection.load(
        faceLandmarksDetection.SupportedPackages.mediapipeFacemesh,
        { maxFaces: MAX_FACES }
    );

    console.log("FaceMesh Model Loaded");

    canvas = document.getElementById('output-canvas');
    ctx = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    video.width = video.videoWidth;
    video.height = video.videoHeight;
}

/**
 * Main render loop - detects faces and emotions.
 */
async function renderPrediction() {
    if (!isRunning) return;

    const predictions = await model.estimateFaces({
        input: video,
        returnTensors: false,
        flipHorizontal: false,
        predictIrises: true
    });

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (predictions.length > 0) {
        predictions.forEach(prediction => {
            const keypoints = prediction.scaledMesh;

            // Draw keypoints
            drawKeypoints(keypoints, ctx);

            // Detect and display emotion
            const emotion = detectEmotion(keypoints);
            if (emotion !== currentEmotion) {
                currentEmotion = emotion;
                updateEmotionDisplay(emotion);
                sendEmotionToBackend(emotion); // Notify Python backend
            }
        });
    } else {
        // No face detected
        if (currentEmotion !== 'neutral') {
            currentEmotion = 'neutral';
            updateEmotionDisplay('neutral');
        }
    }

    rafID = requestAnimationFrame(renderPrediction);
}

/**
 * Detects emotion based on facial landmarks.
 */
function detectEmotion(keypoints) {
    // Get key landmark positions
    const upperLip = keypoints[LANDMARK_INDICES.UPPER_LIP_TOP];
    const lowerLip = keypoints[LANDMARK_INDICES.LOWER_LIP_BOTTOM];
    const leftLipCorner = keypoints[LANDMARK_INDICES.LEFT_LIP_CORNER];
    const rightLipCorner = keypoints[LANDMARK_INDICES.RIGHT_LIP_CORNER];
    const upperLipCenter = keypoints[LANDMARK_INDICES.UPPER_LIP_CENTER];

    const leftEyebrowInner = keypoints[LANDMARK_INDICES.LEFT_EYEBROW_INNER];
    const rightEyebrowInner = keypoints[LANDMARK_INDICES.RIGHT_EYEBROW_INNER];

    const leftEyeTop = keypoints[LANDMARK_INDICES.LEFT_EYE_TOP];
    const leftEyeBottom = keypoints[LANDMARK_INDICES.LEFT_EYE_BOTTOM];
    const rightEyeTop = keypoints[LANDMARK_INDICES.RIGHT_EYE_TOP];
    const rightEyeBottom = keypoints[LANDMARK_INDICES.RIGHT_EYE_BOTTOM];

    const noseTip = keypoints[LANDMARK_INDICES.NOSE_TIP];
    const chin = keypoints[LANDMARK_INDICES.CHIN];

    // Calculate face height for normalization
    const faceHeight = Math.abs(chin[1] - keypoints[LANDMARK_INDICES.FOREHEAD_CENTER][1]);

    // --- SMILE DETECTION ---
    // Lip corners go UP relative to the center of the lips
    const lipCenterY = (upperLip[1] + lowerLip[1]) / 2;
    const leftCornerLift = lipCenterY - leftLipCorner[1];
    const rightCornerLift = lipCenterY - rightLipCorner[1];
    const averageCornerLift = (leftCornerLift + rightCornerLift) / 2;
    const smileRatio = averageCornerLift / faceHeight;

    // Mouth width increases when smiling
    const mouthWidth = Math.abs(rightLipCorner[0] - leftLipCorner[0]);
    const mouthWidthRatio = mouthWidth / faceHeight;

    // --- SAD DETECTION ---
    // Lip corners go DOWN
    const sadRatio = -smileRatio; // Negative of smile

    // --- SURPRISE DETECTION ---
    // Mouth opens wide (vertical distance increases)
    const mouthOpenness = Math.abs(lowerLip[1] - upperLip[1]);
    const mouthOpennessRatio = mouthOpenness / faceHeight;

    // Eyes open wider
    const leftEyeOpenness = Math.abs(leftEyeBottom[1] - leftEyeTop[1]);
    const rightEyeOpenness = Math.abs(rightEyeBottom[1] - rightEyeTop[1]);
    const avgEyeOpenness = (leftEyeOpenness + rightEyeOpenness) / 2;
    const eyeOpennessRatio = avgEyeOpenness / faceHeight;

    // Eyebrows raised (higher than usual)
    const leftEyebrowHeight = noseTip[1] - leftEyebrowInner[1];
    const rightEyebrowHeight = noseTip[1] - rightEyebrowInner[1];
    const avgEyebrowHeight = (leftEyebrowHeight + rightEyebrowHeight) / 2;
    const eyebrowHeightRatio = avgEyebrowHeight / faceHeight;

    // --- EMOTION CLASSIFICATION ---
    // Thresholds (tuned for typical expressions)
    const SMILE_THRESHOLD = 0.012;
    const SAD_THRESHOLD = 0.008;
    const SURPRISE_MOUTH_THRESHOLD = 0.08;
    const SURPRISE_EYE_THRESHOLD = 0.045;

    // --- ANGRY DETECTION ---
    // Eyebrows come together (furrowed) and lower
    const eyebrowDistance = Math.abs(rightEyebrowInner[0] - leftEyebrowInner[0]);
    const eyebrowDistanceRatio = eyebrowDistance / faceHeight;

    // Eyebrows lowered (closer to eyes)
    const leftEyebrowToEye = leftEyebrowInner[1] - leftEyeTop[1];
    const rightEyebrowToEye = rightEyebrowInner[1] - rightEyeTop[1];
    const avgEyebrowToEye = (leftEyebrowToEye + rightEyebrowToEye) / 2;
    const eyebrowLoweredRatio = avgEyebrowToEye / faceHeight;

    // --- TENSED DETECTION ---
    // Lips pressed together (small mouth opening)
    const lipsPressedRatio = mouthOpenness / faceHeight;

    // Eyes slightly narrowed
    const eyeNarrowRatio = avgEyeOpenness / faceHeight;

    // Thresholds for angry and tensed
    const ANGRY_EYEBROW_DISTANCE_THRESHOLD = 0.12; // Eyebrows close together
    const ANGRY_EYEBROW_LOWERED_THRESHOLD = 0.02; // Eyebrows lowered toward eyes
    const TENSED_LIP_THRESHOLD = 0.025; // Lips pressed
    const TENSED_EYE_THRESHOLD = 0.035; // Eyes slightly narrowed

    // Check for surprise first (most distinctive)
    if (mouthOpennessRatio > SURPRISE_MOUTH_THRESHOLD && eyeOpennessRatio > SURPRISE_EYE_THRESHOLD) {
        return 'surprised';
    }

    // Check for angry (furrowed brows + lowered eyebrows + slight frown)
    if (eyebrowDistanceRatio < ANGRY_EYEBROW_DISTANCE_THRESHOLD &&
        eyebrowLoweredRatio < ANGRY_EYEBROW_LOWERED_THRESHOLD &&
        smileRatio < 0) {
        return 'angry';
    }

    // Check for tensed (lips pressed + eyes narrowed + eyebrows together)
    if (lipsPressedRatio < TENSED_LIP_THRESHOLD &&
        eyeNarrowRatio < TENSED_EYE_THRESHOLD &&
        eyebrowDistanceRatio < 0.15) {
        return 'tensed';
    }

    // Check for smile (happy)
    if (smileRatio > SMILE_THRESHOLD && mouthWidthRatio > 0.35) {
        return 'happy';
    }

    // Check for sad
    if (sadRatio > SAD_THRESHOLD) {
        return 'sad';
    }

    return 'neutral';
}

/**
 * Updates the emoji display on the page.
 */
function updateEmotionDisplay(emotion) {
    const emojiEl = document.getElementById('emotion-emoji');
    const labelEl = document.getElementById('emotion-label');

    if (emojiEl) {
        emojiEl.textContent = EMOTION_EMOJIS[emotion] || EMOTION_EMOJIS.neutral;
        emojiEl.className = `emotion-emoji emotion-${emotion}`;
    }

    if (labelEl) {
        labelEl.textContent = emotion.charAt(0).toUpperCase() + emotion.slice(1);
    }

    // Update Floating Cursor Prompt with Emotion
    const cursorPrompt = document.getElementById('cursorPrompt');
    if (cursorPrompt) {
        if (emotion === "neutral") {
            cursorPrompt.textContent = "Jarvis: Ready";
        } else {
            cursorPrompt.textContent = `Jarvis: User is ${emotion}`;
            cursorPrompt.classList.add('visible');
            setTimeout(() => cursorPrompt.classList.remove('visible'), 2000); // Hide after 2s
        }
    }

    console.log(`Emotion: ${emotion}`);
}

/**
 * Draws facial keypoints.
 */
function drawKeypoints(keypoints, ctx) {
    ctx.fillStyle = '#32EEDB';

    for (let i = 0; i < keypoints.length; i++) {
        const [x, y, z] = keypoints[i];
        ctx.beginPath();
        ctx.arc(x, y, 1, 0, 2 * Math.PI);
        ctx.fill();
    }

    // Highlight emotion-relevant points in different colors
    ctx.fillStyle = '#FF6B6B'; // Red for mouth
    [LANDMARK_INDICES.UPPER_LIP_TOP, LANDMARK_INDICES.LOWER_LIP_BOTTOM,
    LANDMARK_INDICES.LEFT_LIP_CORNER, LANDMARK_INDICES.RIGHT_LIP_CORNER].forEach(idx => {
        const [x, y] = keypoints[idx];
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
    });

    [LANDMARK_INDICES.LEFT_EYEBROW_INNER, LANDMARK_INDICES.RIGHT_EYEBROW_INNER].forEach(idx => {
        const [x, y] = keypoints[idx];
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
    });
}

// --- Main Initialization ---
async function main() {
    // 1. Setup Camera
    try {
        await setupCamera();
        video.play();
        console.log("Camera setup success.");
    } catch (err) {
        console.error("Camera Error:", err);
        alert("Camera Info: " + err.name + " - " + err.message);
        return;
    }

    // 2. Load Model
    try {
        await loadFaceMeshModel();
        console.log("Model loaded success.");
    } catch (err) {
        console.error("Model Error:", err);
        alert("Model Load Error: " + err.message);
        return;
    }

    // 3. Start Loop
    try {
        isRunning = true;
        renderPrediction();
        console.log("FaceMesh System Started!");
    } catch (err) {
        console.error("Render Error:", err);
        alert("Render Error: " + err.message);
    }
}

// Start when DOM is ready
document.addEventListener("DOMContentLoaded", main);