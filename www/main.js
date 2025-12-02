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
}

// ✅ Expose appendUserMessage so Python can use it for spoken commands
eel.expose(appendUserMessage);
function appendUserMessage(message) {
    const chatArea = document.getElementById("receiverTextArea");
    if (!chatArea) {
        console.warn("receiverTextArea not found for appendUserMessage.");
        return;
    }

    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble sender";
    userBubble.innerHTML = `<div class='chat-message user-message'><b>You:</b><br>${message}</div>`;
    chatArea.appendChild(userBubble);
    chatArea.scrollTop = chatArea.scrollHeight;
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
