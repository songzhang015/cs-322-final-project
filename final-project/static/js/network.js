// network.js - handles the data syncing between players
import { applyRemoteEvent, setDrawingEnabled } from "./drawing.js";

let socket = null;

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

	socket.on("startPath", data => applyRemoteEvent("startPath", data));
	socket.on("draw", data => applyRemoteEvent("draw", data));
	socket.on("endPath", () => applyRemoteEvent("endPath"));
	socket.on("fill", data => applyRemoteEvent("fill", data));
	socket.on("undo", () => applyRemoteEvent("undo"));
	socket.on("clear", () => applyRemoteEvent("clear"));

	socket.on("roundPrompt", data => {
		console.log("You are drawing:", data.prompt);
	});

	socket.on("roundStarted", data => {
		console.log("A new round started! You are a guesser.");
		// TODO: display "Guess the drawing!" in UI
	});
}

// Export socket so other modules can emit events
export function getSocket() {
	return socket;
}
