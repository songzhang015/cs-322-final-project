// network.js - handles the data syncing between players
import { applyRemoteEvent } from "./drawing.js";

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

	// Send join event with player info
	socket.emit("join", {
		id: playerData.id, // unique ID per client
		name: playerData.name, // from setup.js
		avatar: playerData.avatar,
	});

	// Listen for updated player list
	socket.on("playerList", (players) => {
		console.log("Updated player list:", players);
	});

	// Listen for round start, drawings, guesses
	socket.on("roundStarted", (data) => {
		console.log("Round started!", data);
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
