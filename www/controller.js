// Function to append Jarvis messages as bubbles to the chat area
function appendJarvisBubble(messageHTML) {
    const area = document.getElementById("receiverTextArea");
    if (!area) return;

    const botBubble = document.createElement("div");
    botBubble.className = "chat-bubble receiver";
    botBubble.innerHTML = `<div class="chat-message jarvis-message"><b>Jarvis:</b><br>${messageHTML}</div>`;
    area.appendChild(botBubble);
    area.scrollTop = area.scrollHeight;
}

// Function to handle file downloads and display completion message in chat
eel.expose(downloadCompletedFile);
function downloadCompletedFile(base64_data, filename) {
    // 1. Trigger actual download
    const blobURL = 'data:application/octet-stream;base64,' + base64_data;
    const link = document.createElement('a');
    link.href = blobURL;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // 2. Show completion message in the chat area as a Jarvis bubble.
    // This ensures it appears consistently with other chat messages.
    appendJarvisBubble("✅ <strong>Document</strong> completed and downloaded.");

    // The eel.DisplayMessage call for "Downloading..." has been removed from here.
    // If a transient "Downloading..." status is needed, it should be handled
    // by the Python backend explicitly calling a chat function like appendJarvisBubble
    // (for a temporary chat message) or by updating a dedicated status UI element.
}

// Function to append user messages as bubbles to the chat area
// This function is crucial for user messages to appear in the chat history.
function appendUserMessage(message) {
    const area = document.getElementById("receiverTextArea");
    if (!area) return;

    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble sender";
    userBubble.innerHTML = `<div class='chat-message user-message'><b>You:</b><br>${message}</div>`;
    area.appendChild(userBubble);
    area.scrollTop = area.scrollHeight;
}

// Updated receiverText function to correctly handle chat messages
eel.expose(receiverText);
function receiverText(responseText) {
    const area = document.getElementById("receiverTextArea");
    if (!area) {
        console.warn("receiverTextArea not found");
        return;
    }

    const userInput = window.lastUserInput || "";

    // Only show user input if not an initialization message and if there was actual input
    if (userInput && !responseText.toLowerCase().includes("initializing jarvis")) {
        const userBubble = document.createElement("div");
        userBubble.className = "chat-bubble sender";
        userBubble.innerHTML = `<div class='chat-message user-message'><b>You:</b><br>${userInput}</div>`;
        area.appendChild(userBubble);
        window.lastUserInput = ""; // Clear last user input after displaying it
    }

    // Jarvis bubble
    const botBubble = document.createElement("div");
    botBubble.className = "chat-bubble receiver";
    botBubble.innerHTML = `<div class='chat-message jarvis-message'><b>Jarvis:</b><br>${responseText}</div>`;
    area.appendChild(botBubble);

    area.scrollTop = area.scrollHeight;
}

function sendTextCommand() {
    const input = document.getElementById("textCommandInput").value.trim();
    if (input !== "") {
        // Save input globally so receiverText can use it
        window.lastUserInput = input;

        // Send to backend
        eel.receive_text_command(input);

        // Show in chat immediately
        appendUserMessage(input);

        // Clear input field
        document.getElementById("textCommandInput").value = "";
    }
}

document.getElementById("textCommandInput").addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        sendTextCommand();
    }
});
