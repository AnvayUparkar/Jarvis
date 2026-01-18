// main.js

// Function to send chat input to Python
document.getElementById("SendBtn").onclick = function () {
    const message = document.getElementById("chatbox").value.trim();
    if (message === "") return;

    window.lastUserInput = message;  // ⬅️ Needed to show in bubble
    appendUserMessage(message);      // Display user message immediately
    eel.handle_command_from_frontend(message)();  // Send to Python
    document.getElementById("chatbox").value = "";
};

// Mic Button
document.getElementById("MicBtn").onclick = function () {
    if (typeof eel.listen_from_frontend === 'function') {
        eel.listen_from_frontend();
    } else {
        console.warn("listen_from_frontend not found.");
    }
};

// Press Enter to send
document.getElementById("chatbox").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        document.getElementById("SendBtn").click();
    }
});

// File Attach (clicks hidden input)
document.getElementById("AttachBtn").onclick = function () {
    document.getElementById("FileInput").click();
};

document.getElementById("FileInput").onchange = function (event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64Content = e.target.result.split(',')[1];
            const filename = file.name;
            const mimetype = file.type;

            try {
                await eel.upload_attachment(filename, base64Content, mimetype)();
                addChatBubble("sender", `Sent file: ${filename}`);
            } catch (error) {
                console.error("Error uploading file:", error);
                addChatBubble("receiver", "Error uploading file. Please try again.");
            }
        };
        reader.readAsDataURL(file);
    } else {
        addChatBubble("receiver", "No file selected for upload.");
    }
};


// === EXPOSED JS FUNCTIONS FOR PYTHON TO CALL ===

eel.expose(DisplayMessage);
function DisplayMessage(text) {
    const element = document.getElementById("receiverText");
    if (element) {
        element.innerHTML = text;
    } else {
        console.warn("Element with ID 'receiverText' not found for DisplayMessage.");
    }
}

eel.expose(receiverText);
function receiverText(responseText) {
    const area = document.getElementById("receiverTextArea");
    if (!area) {
        console.warn("receiverTextArea not found");
        return;
    }

    const botBubble = document.createElement("div");
    botBubble.className = "chat-bubble receiver";
    botBubble.innerHTML = `<div class='chat-message jarvis-message'><b>Jarvis:</b><br>${responseText}</div>`;
    area.appendChild(botBubble);
    area.scrollTop = area.scrollHeight;

    // Re-render MathJax if available (for LaTeX math rendering)
    if (window.MathJax && window.MathJax.typesetPromise) {
        MathJax.typesetPromise([botBubble]).catch(err => console.log('MathJax rendering error:', err));
    }
}

// ✅ Expose appendUserMessage so Python can use it for spoken commands
// (Note: This function is internally overridden later in the file for sentiment analysis)
eel.expose(appendUserMessage);
function appendUserMessage(message) {
    console.log("appendUserMessage called via Eel");
    // Forward to the latest global implementation (which includes sentiment analysis)
    if (window.appendUserMessageImpl) {
        window.appendUserMessageImpl(message);
    }
}

// Show Image
eel.expose(showImage);
function showImage(base64Image) {
    const imageElement = document.getElementById("generated-image");
    if (imageElement) {
        imageElement.src = base64Image;
        imageElement.style.display = "block";
    } else {
        console.error("Image element not found: 'generated-image'");
    }
}

// Hide Image
eel.expose(hideImage);
function hideImage() {
    const imageElement = document.getElementById("generated-image");
    if (imageElement) {
        imageElement.style.display = "none";
    }
}

// Siri Wave Display Toggle
eel.expose(ShowSiriWave);
function ShowSiriWave() {
    const siriContainer = document.getElementById("siri-container");
    if (siriContainer) {
        siriContainer.hidden = false;
    } else {
        console.warn("Siri Wave container with ID 'siri-container' not found.");
    }
}
eel.expose(HideSiriWave);
function HideSiriWave() {
    const siriContainer = document.getElementById("siri-container");
    if (siriContainer) {
        siriContainer.hidden = true;
    }
}

// Loader Toggle
eel.expose(ShowLoader);
function ShowLoader() {
    const loaderElement = document.getElementById("Loader");
    if (loaderElement) {
        loaderElement.hidden = false;
    } else {
        console.warn("Loader element with ID 'Loader' not found.");
    }
}
eel.expose(HideLoader);
function HideLoader() {
    const loaderElement = document.getElementById("Loader");
    if (loaderElement) {
        loaderElement.hidden = true;
    }
}

// Typing Indicator Toggle
eel.expose(ShowTyping);
function ShowTyping() {
    const typingDots = document.getElementById("TypingDots");
    if (typingDots) {
        typingDots.hidden = false;
    } else {
        console.warn("TypingDots element with ID 'TypingDots' not found.");
    }
}
eel.expose(HideTyping);
function HideTyping() {
    const typingDots = document.getElementById("TypingDots");
    if (typingDots) {
        typingDots.hidden = true;
    }
}

// Voice preview text
eel.expose(VoicePreview);
function VoicePreview(text) {
    const voicePreviewArea = document.getElementById("VoicePreviewArea");
    if (voicePreviewArea) {
        voicePreviewArea.innerText = text;
    } else {
        console.warn("VoicePreviewArea element with ID 'VoicePreviewArea' not found.");
    }
}

// Helper function to add general chat bubbles
function addChatBubble(type, text) {
    const area = document.getElementById("receiverTextArea");
    if (!area) {
        console.warn("receiverTextArea not found for addChatBubble.");
        return;
    }
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${type}`;
    const msg = document.createElement("div");
    msg.className = "chat-message";
    if (type === "sender") {
        msg.innerHTML = `<b>You:</b><br>${text}`;
    } else if (type === "receiver") {
        msg.innerHTML = `<b>Jarvis:</b><br>${text}`;
    } else {
        msg.innerHTML = text;
    }

    bubble.appendChild(msg);
    area.appendChild(bubble);
    area.scrollTop = area.scrollHeight;
}

// Download file sent from Python
eel.expose(downloadCompletedFile);
function downloadCompletedFile(base64_data, filename) {
    const blobURL = 'data:application/octet-stream;base64,' + base64_data;
    const link = document.createElement('a');
    link.href = blobURL;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addChatBubble("receiver", `✅ <strong>${filename}</strong> has been generated and downloaded.`);
    DisplayMessage(`Downloading ${filename}...`);
}

// Text input submission for other use cases
eel.expose(submitTextInput);
function submitTextInput() {
    const textInputBox = document.getElementById("textInputBox");
    if (textInputBox) {
        const contact = textInputBox.value;
        eel.ReceiveInputText(contact);
        textInputBox.value = "";
    } else {
        console.warn("textInputBox not found for submitTextInput.");
    }
}

// Generic alert prompt from Python
eel.expose(displayPrompt);
function displayPrompt(text) {
    alert(text);
}

// ----------------------------------------------------
// 🧠 AVATAR VIDEO CONTROLLER (STATE MACHINE)
// ----------------------------------------------------
// ----------------------------------------------------
// 🖼️ STATIC AVATAR IMAGE CONTROLLER
// Displays avatar.jpg in glow circle, lip-sync video overlays on top
// ----------------------------------------------------
class AvatarImage {
    constructor() {
        this.container = document.getElementById("avatar-container");
        this.isSpeaking = false;
        this.currentEmotion = "neutral";

        if (this.container) {
            this.init();
        } else {
            console.warn("[AVATAR] Container not found, retrying in 500ms...");
            setTimeout(() => this.init(), 500);
        }
    }

    init() {
        this.container = document.getElementById("avatar-container");
        if (!this.container) {
            console.error("[AVATAR] avatar-container not found!");
            return;
        }

        console.log("[AVATAR] Initializing static image avatar...");

        // Clear container
        this.container.innerHTML = "";

        // Create image element for avatar.jpg (shows by default, hidden when video plays)
        this.avatarImg = document.createElement("img");
        this.avatarImg.id = "avatar-image";
        this.avatarImg.src = "assets/img/avatar.jpg";
        this.avatarImg.alt = "MIRAGE Avatar";
        this.avatarImg.style.cssText = `
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
            display: block;
        `;

        // Error handling
        this.avatarImg.onerror = () => {
            console.error("[AVATAR] Failed to load avatar.jpg");
            this.container.innerHTML = "<p style='color:#fff;text-align:center;padding-top:40%;'>Avatar not found</p>";
        };

        this.avatarImg.onload = () => {
            console.log("[AVATAR] ✅ avatar.jpg loaded successfully");
        };

        this.container.appendChild(this.avatarImg);
    }

    // Emotion methods (for compatibility with existing code)
    setEmotion(sentiment) {
        console.log(`[AVATAR] Emotion: ${sentiment}`);
        this.currentEmotion = sentiment;
    }

    // Speech signaling methods
    startSpeaking() {
        this.isSpeaking = true;
        console.log("[AVATAR] Speech Signaling: START");
    }

    stopSpeaking() {
        this.isSpeaking = false;
        console.log("[AVATAR] Speech Signaling: STOP");
    }

    // Placeholder for audio blob (lip-sync handles this now)
    playAudioBlob(base64String) {
        console.log("[AVATAR] Audio blob received (handled by lip-sync system)");
    }
}

// Global Instance
const avatar = new AvatarImage();


// Exposed function for Python to control Avatar/Play Audio
eel.expose(play_audio_blob);
function play_audio_blob(base64_audio) {
    try {
        if (avatar) {
            avatar.playAudioBlob(base64_audio);
        }
    } catch (e) {
        console.error("play_audio_blob error:", e);
    }
}

// Legacy support for state calls (mapped to emotions fallback)
eel.expose(js_play_avatar_video);
function js_play_avatar_video(stateName) {
    if (!avatar) return;
    // Map old video states to emotions/actions
    if (stateName === "HAPPY") avatar.setEmotion("happy");
    if (stateName === "SAD") avatar.setEmotion("sad");
    if (stateName === "IDLE") avatar.setEmotion("neutral");
}

// ----------------------------------------------------
// 🎬 WAV2LIP LIP-SYNC VIDEO PLAYER
// ----------------------------------------------------

// Helper function to show/hide avatar elements
function setAvatarVisibility(show) {
    const container = document.getElementById("avatar-container");
    if (!container) return;

    const avatarImg = container.querySelector("#avatar-image");
    const video = container.querySelector("#lipsync-video");

    if (show) {
        // Show avatar, hide video
        if (avatarImg) avatarImg.style.display = "block";
        if (video) video.style.display = "none";
    } else {
        // Hide avatar, show video
        if (avatarImg) avatarImg.style.display = "none";
        if (video) video.style.display = "block";
    }
}

eel.expose(play_lipsync_video);
function play_lipsync_video(videoPath) {
    console.log("[LIPSYNC] Playing video:", videoPath);

    const container = document.getElementById("avatar-container");
    if (!container) {
        console.error("[LIPSYNC] avatar-container not found!");
        return;
    }

    // Hide avatar image immediately
    setAvatarVisibility(false);

    // Create or reuse video element
    let video = container.querySelector("#lipsync-video");
    if (!video) {
        video = document.createElement("video");
        video.id = "lipsync-video";
        video.style.cssText = `
            width: calc(100% - 20px);
            height: calc(100% - 20px);
            object-fit: cover;
            border-radius: 50%;
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 10;
        `;
        video.autoplay = true;
        video.muted = true; // Mute video since audio plays separately via pygame
        video.playsInline = true;

        // Restore avatar image when video ends
        video.onended = () => {
            console.log("[LIPSYNC] Video ended, restoring avatar image");
            setAvatarVisibility(true);
        };

        video.onerror = (e) => {
            console.error("[LIPSYNC] Video error:", e);
            setAvatarVisibility(true);
        };

        container.appendChild(video);
    }

    // Make sure video is visible
    video.style.display = "block";

    // Add cache-busting parameter to ensure fresh video loads
    const timestamp = new Date().getTime();
    video.src = videoPath + "?t=" + timestamp;

    // Force load and play
    video.load();
    video.play().then(() => {
        console.log("[LIPSYNC] Video playback started");
    }).catch(e => {
        console.error("[LIPSYNC] Play failed:", e);
        setAvatarVisibility(true);
    });
}

// ----------------------------------------------------
// 🧠 SENTIMENT ANALYSIS INTEGRATION
// ----------------------------------------------------

async function analyzeSentiment(text) {
    if (!text || text.trim() === "") return;

    console.log(`[SENTIMENT] Analyzing: "${text}"`);

    try {
        const response = await fetch("http://localhost:5001/sentiment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`[SENTIMENT] Result: ${data.sentiment} (Conf: ${data.confidence})`);

        // Update Avatar
        avatar.setEmotion(data.sentiment);

    } catch (error) {
        console.error("[SENTIMENT] Failed:", error);
        // Fallback to Neutral/Idle
    }
}

// ----------------------------------------------------
// 🔌 EEL EXPOSURES FOR BACKEND SYNCHRONIZATION
// ----------------------------------------------------

eel.expose(signal_speech_start);
function signal_speech_start() {
    try {
        if (avatar && typeof avatar.startSpeaking === 'function') {
            avatar.startSpeaking();
        }
    } catch (e) {
        console.error("signal_speech_start error:", e);
    }
}

eel.expose(signal_speech_end);
function signal_speech_end() {
    try {
        if (avatar && typeof avatar.stopSpeaking === 'function') {
            avatar.stopSpeaking();
        }
    } catch (e) {
        console.error("signal_speech_end error:", e);
    }
}

// Override the existing appendUserMessage to inject sentiment analysis
// The original was defined earlier or in other files, but we can overwrite/extend behavior here
// We need to keep the UI update and ADD the analysis.
const originalAppendUserMessage = window.appendUserMessage || (() => { });

// Re-expose/Refine appendUserMessage
// Re-expose/Refine appendUserMessage implementation
window.appendUserMessageImpl = function (message) {
    const chatArea = document.getElementById("receiverTextArea");
    if (!chatArea) return;

    // UI Update
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble sender";
    userBubble.innerHTML = `<div class='chat-message user-message'><b>You:</b><br>${message}</div>`;
    chatArea.appendChild(userBubble);
    chatArea.scrollTop = chatArea.scrollHeight;

    // NEW: Trigger Sentiment Analysis
    analyzeSentiment(message);
};

// Override the previous function just in case
appendUserMessage = window.appendUserMessageImpl;
