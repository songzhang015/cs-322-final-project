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

	// Listen for round start, drawings, guesses
	socket.on("roundStarted", (data) => {
		console.log("Round started!", data);

		// Clear timer
		if (roundTimer) clearInterval(roundTimer);
		roundTimeLeft = data.remaining ?? ROUND_TIME;

		const timerTextEl = document.querySelector(".timer-text");
		if (timerTextEl) timerTextEl.textContent = roundTimeLeft;

		// === TIMER START ===
		roundTimer = setInterval(() => {
			roundTimeLeft--;
			if (timerTextEl) timerTextEl.textContent = roundTimeLeft;

			if (roundTimeLeft <= 0) {
				clearInterval(roundTimer);
				socket.emit("forceRoundEnd");
			}
		}, 1000);

        const line1 = document.querySelector(".prompt-line1");
        const line2 = document.querySelector(".prompt-line2");

        if (line1) line1.textContent = "";
        if (line2) line2.textContent = "";

		const toolbar = document.querySelector(".play-drawtools");

		if (data.role === "drawer") {
			setDrawingEnabled(true);
			toolbar.classList.remove("hidden");
			toolbar.classList.add("active");
		} else {
			setDrawingEnabled(false);
			toolbar.classList.add("hidden");
			toolbar.classList.remove("active");
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
