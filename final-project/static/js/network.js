// network.js - handles the data syncing between players
import { applyRemoteEvent, setDrawingEnabled } from "./drawing.js";

const ROUND_TIME = 20;
let socket = null;
let roundTimer = null;
let roundTimeLeft = ROUND_TIME;

export function connectToServer(playerData, onConnected) {
    socket = io();

    socket.on("connect", () => {
        socket.emit("join", {
            id: playerData.id,
            name: playerData.name,
            avatar: playerData.avatar,
        });

        if (onConnected) onConnected(socket);
    });

	// Listen for updated player list
	socket.on("playerList", (players) => {
		console.log("Updated player list:", players);
	});

	// === PHASE 1: roundStarting ===
	socket.on("roundStarting", () => {
		console.log("Round is preparing…");

		// Stop timer
		if (roundTimer) clearInterval(roundTimer);
		roundTimer = null;
		roundTimeLeft = 0;

		// Clear timer UI
		const timerTextEl = document.querySelector(".timer-text");
		if (timerTextEl) timerTextEl.textContent = "";

		// Clear prompt banner
		const line1 = document.querySelector(".prompt-line1");
		const line2 = document.querySelector(".prompt-line2");
		if (line1) line1.textContent = "";
		if (line2) line2.textContent = "";

		// Hide draw tools until true round start
		const toolbar = document.querySelector(".play-drawtools");
		if (toolbar) {
			toolbar.classList.add("hidden");
			toolbar.classList.remove("active");
		}
	});

	// === PHASE 2: roundStarted ===
	socket.on("roundStarted", (data) => {
		console.log("Round started!", data);

		// Reset timer
		if (roundTimer) clearInterval(roundTimer);
		roundTimer = null;

		roundTimeLeft = data.remaining ?? ROUND_TIME;

		const timerTextEl = document.querySelector(".timer-text");
		if (timerTextEl) timerTextEl.textContent = roundTimeLeft;

		// clear prompt text (roundPrompt will fill it)
		const line1 = document.querySelector(".prompt-line1");
		const line2 = document.querySelector(".prompt-line2");
		if (line1) line1.textContent = "";
		if (line2) line2.textContent = "";

		const toolbar = document.querySelector(".play-drawtools");

		const isDrawer = data.role === "drawer";

		if (isDrawer) {
			setDrawingEnabled(true);
			if (toolbar) {
				toolbar.classList.remove("hidden");
				toolbar.classList.add("active");
			}

			// === ONLY THE DRAWER RUNS THE AUTHORITATIVE TIMER ===
			roundTimer = setInterval(() => {
				roundTimeLeft--;
				if (timerTextEl) timerTextEl.textContent = roundTimeLeft;

				if (roundTimeLeft <= 0) {
					clearInterval(roundTimer);
					roundTimer = null;

					// Only drawer ends the round
					socket.emit("forceRoundEnd");
				}
			}, 1000);
		} else {
			// Guessers see countdown but do not emit forceRoundEnd
			setDrawingEnabled(false);
			if (toolbar) {
				toolbar.classList.add("hidden");
				toolbar.classList.remove("active");
			}

			// === DISPLAY-ONLY TIMER FOR GUESSERS ===
			roundTimer = setInterval(() => {
				roundTimeLeft--;
				if (timerTextEl) timerTextEl.textContent = roundTimeLeft;

				// Guessers DO NOT emit forceRoundEnd
				if (roundTimeLeft <= 0) {
					clearInterval(roundTimer);
					roundTimer = null;
				}
			}, 1000);
		}
	});



	socket.on("lobbyReset", () => {
		console.log("Lobby reset — stopping timer and clearing UI.");

		// Stop timer
		if (roundTimer) clearInterval(roundTimer);
		roundTimer = null;
		roundTimeLeft = 0;

		// Clear timer UI
		const timerTextEl = document.querySelector(".timer-text");
		if (timerTextEl) timerTextEl.textContent = "";

		// Clear header lines
		const line1 = document.querySelector(".prompt-line1");
		const line2 = document.querySelector(".prompt-line2");
		if (line1) line1.textContent = "";
		if (line2) line2.textContent = "";

		// Hide draw tools (nobody should be drawing now)
		const toolbar = document.querySelector(".play-drawtools");
		if (toolbar) {
			toolbar.classList.add("hidden");
			toolbar.classList.remove("active");
		}
	});


	socket.on("startPath", data => applyRemoteEvent("startPath", data));
	socket.on("draw", data => applyRemoteEvent("draw", data));
	socket.on("endPath", () => applyRemoteEvent("endPath"));
	socket.on("fill", data => applyRemoteEvent("fill", data));
	socket.on("undo", () => applyRemoteEvent("undo"));
	socket.on("clear", () => applyRemoteEvent("clear"));
}

// Export socket so other modules can emit events
export function getSocket() {
	return socket;
}
