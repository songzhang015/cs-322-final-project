// network.js - Updated timer logic
import { applyRemoteEvent, setDrawingEnabled } from "./drawing.js";
import { updateScoreboard } from "./setup.js";

const ROUND_TIME = 20;
let socket = null;
let roundTimer = null;
let roundStartTime = null; // <-- NEW: Store when round started

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

	socket.on("playerList", (players) => {
		updateScoreboard(players);
	});

	socket.on("roundStarting", () => {
		console.log("Round is preparing…");

		// Stop timer
		if (roundTimer) clearInterval(roundTimer);
		roundTimer = null;
		roundStartTime = null;
		
		setDrawingEnabled(false);

		// Clear timer UI
		const timerTextEl = document.querySelector(".timer-text");
		if (timerTextEl) timerTextEl.textContent = "";

		// Clear prompt banner
		const line1 = document.querySelector(".prompt-line1");
		const line2 = document.querySelector(".prompt-line2");
		if (line1) line1.textContent = "";
		if (line2) line2.textContent = "";

		const toolbar = document.querySelector(".play-drawtools");
		if (toolbar) {
			toolbar.classList.add("hidden");
			toolbar.classList.remove("active");
		}
	});

	socket.on("roundStarted", (data) => {
		console.log("Round started!", data);

		// Stop any existing timer
		if (roundTimer) clearInterval(roundTimer);
		roundTimer = null;

		// Store when the round started (server timestamp in seconds)
		roundStartTime = data.startTime;

		const timerTextEl = document.querySelector(".timer-text");
		const toolbar = document.querySelector(".play-drawtools");
		const isDrawer = data.role === "drawer";

		if (isDrawer) {
			if (toolbar && typeof toolbar.regeneratePalette === "function") {
				toolbar.regeneratePalette();
			}

			setDrawingEnabled(true);
			if (toolbar) {
				toolbar.classList.remove("hidden");
				toolbar.classList.add("active");
			}
		} else {
			setDrawingEnabled(false);
			if (toolbar) {
				toolbar.classList.add("hidden");
				toolbar.classList.remove("active");
			}
		}

		// === NEW: CALCULATED TIMER (works for both drawer and guessers) ===
		function updateTimer() {
			const now = Date.now() / 1000; // Current time in seconds
			const elapsed = now - roundStartTime;
			const remaining = Math.max(0, Math.ceil(ROUND_TIME - elapsed));

			if (timerTextEl) timerTextEl.textContent = remaining;

			// Only drawer emits round end
			if (remaining <= 0) {
				clearInterval(roundTimer);
				roundTimer = null;
				
				if (isDrawer) {
					socket.emit("forceRoundEnd");
				}
			}
		}

		// Update immediately
		updateTimer();

		// Then update every 100ms for smooth countdown
		roundTimer = setInterval(updateTimer, 100);
	});

	socket.on("lobbyReset", () => {
		console.log("Lobby reset — stopping timer and clearing UI.");

		if (roundTimer) clearInterval(roundTimer);
		roundTimer = null;
		roundStartTime = null;

		const timerTextEl = document.querySelector(".timer-text");
		if (timerTextEl) timerTextEl.textContent = "";

		const line1 = document.querySelector(".prompt-line1");
		const line2 = document.querySelector(".prompt-line2");
		if (line1) line1.textContent = "";
		if (line2) line2.textContent = "";

		const toolbar = document.querySelector(".play-drawtools");
		if (toolbar) {
			toolbar.classList.add("hidden");
			toolbar.classList.remove("active");
		}
	});

	socket.on("startPath", data => applyRemoteEvent("startPath", data));
	socket.on("draw", data => applyRemoteEvent("draw", data));
	socket.on("dot", data => applyRemoteEvent("dot", data));
	socket.on("endPath", () => applyRemoteEvent("endPath"));
	socket.on("fill", data => applyRemoteEvent("fill", data));
	socket.on("undo", () => {});
	socket.on("clear", () => applyRemoteEvent("clear"));
}

export function getSocket() {
	return socket;
}