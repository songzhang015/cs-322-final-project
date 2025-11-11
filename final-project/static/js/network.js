// network.js - handles the data syncing between players

let socket = null;

export function connectToServer(playerData) {
	socket = io();

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

	// Optional: listen for round start, drawings, guesses later
	socket.on("roundStarted", (data) => {
		console.log("Round started!", data);
	});
}

// Export socket so other modules can emit events
export function getSocket() {
	return socket;
}
