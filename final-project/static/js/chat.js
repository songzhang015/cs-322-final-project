// chat.js - handles chat and guessing prompts
import { getSocket } from "./network.js";

export function initChatDOM(chatContainer) {
    const chatHistory = document.createElement("div");
    chatHistory.classList.add("chat-history");

    const chatInput = document.createElement("input");
    chatInput.classList.add("chat-input");
    chatInput.placeholder = "Type your guess or message...";
    chatInput.maxLength = 128;

    chatContainer.append(chatHistory, chatInput);

    const socket = getSocket();
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            const msg = chatInput.value.trim();
            if (!msg) return;

            socket.emit("chatMessage", { message: msg });
            chatInput.value = "";
        }
    });

    socket.on("chatMessage", (data) => {
        const msg = document.createElement("div");

        // Style by zone
        if (data.sender_zone === 1) {
            msg.classList.add("zone1");
        } else {
            msg.classList.add("zone2");
        }

        msg.classList.add("chat-message");

        // NEW: system messages = red text, no name prefix
        if (data.type === "correct") {
            msg.classList.add("chat-correct");
            msg.textContent = `${data.name} guessed the word!`;
        }
        else if (data.type === "leave") {
            msg.classList.add("chat-leave");
            msg.textContent = `${data.message}`;
        }
        else if (data.type === "reveal") {
            msg.classList.add("chat-reveal");
            msg.textContent = `The word was ${data.word}!`;
        }
        else {
            // Normal chat
            msg.textContent = `${data.name}: ${data.message}`;
        }

        chatHistory.append(msg);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    });

    socket.on("correctGuess", (data) => {
        const sys = document.createElement("div");
        sys.classList.add("chat-system");
        sys.textContent = `${data.name} guessed the word!`;
        chatHistory.append(sys);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    });

    socket.on("roundPrompt", (data) => {
        const line1 = document.querySelector(".prompt-line1");
        const line2 = document.querySelector(".prompt-line2");
        if (!line1 || !line2) return;

        if (data.role === "drawer") {
            const sys = document.createElement("div");
            sys.classList.add("chat-system");
            sys.textContent = `You are drawing: ${data.prompt}`;
            chatHistory.append(sys);
            chatHistory.scrollTop = chatHistory.scrollHeight;

            line1.textContent = "Draw the prompt:";
            line2.textContent = data.prompt;

        } else {
            // === FULLY SECURE GUESSER MODE ===
            // Guessers receive ONLY length
            const underscores = Array(data.length).fill("_").join(" ");
            line1.textContent = "Guess the word:";
            line2.textContent = underscores;
        }
    });

    socket.on("waitingForPlayers", (data) => {
        const sys = document.createElement("div");
        sys.classList.add("chat-system");
        sys.textContent = data.message;
        chatHistory.append(sys);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    });

    socket.on("roundStarting", () => {
        const sys = document.createElement("div");
        sys.classList.add("chat-system");
        sys.textContent = "New round starting!";
        chatHistory.append(sys);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    });
}