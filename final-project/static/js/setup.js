// setup.js - initializes the game and name + avatar creation

function init() {
	let name = "";

	const gameHeader = document.createElement("img");
	gameHeader.src = "/static/images/logo.png";
	gameHeader.alt = "drawing game";
	gameHeader.classList.add("game-header");

	const formContainer = document.createElement("div");
	formContainer.classList.add("form-container");

	const nameForm = document.createElement("form");

	const nameInput = document.createElement("input");
	nameInput.classList.add("name-input");
	nameInput.placeholder = "Enter your name";

	const startBtn = document.createElement("button");
	startBtn.classList.add("start-btn");
	startBtn.textContent = "Start!";

	startBtn.addEventListener("click", function (e) {
		e.preventDefault();
		name = nameInput.value;
		if (1) {
			// If name is valid - not empty, not too long
			nameForm.classList.add("move-off");
			initAvatar(formContainer);
		}
	});

	document.body.append(gameHeader);
	document.body.append(formContainer);
	formContainer.append(nameForm);
	nameForm.append(nameInput);
	nameForm.append(startBtn);
}

function initAvatar(formContainer) {
	const avatarForm = document.createElement("form");

	const avatarHeader = document.createElement("h1");
	avatarHeader.classList.add("avatar-header");
	avatarHeader.textContent = "Create your avatar";

	const avatarContainer = document.createElement("div");
	avatarContainer.classList.add("avatar-container");

	const avatarDisplayContainer = document.createElement("div");
	avatarDisplayContainer.classList.add("avatar-display-container");

	const avatarSelectionContainer = document.createElement("div");
	avatarSelectionContainer.classList.add("avatar-selection-container");

	const avatarDisplay = document.createElement("h1");
	avatarDisplay.classList.add("avatar-display");
	avatarDisplay.textContent = "Display";

	const avatarEye = document.createElement("h2");
	avatarEye.classList.add("avatar-eye");
	avatarEye.textContent = "E";

	const avatarMouth = document.createElement("h2");
	avatarMouth.classList.add("avatar-eye");
	avatarMouth.textContent = "M";

	const avatarColor = document.createElement("h2");
	avatarColor.classList.add("avatar-eye");
	avatarColor.textContent = "C";

	const startBtn = document.createElement("button");
	startBtn.classList.add("start-btn");
	startBtn.textContent = "Play!";

	formContainer.append(avatarForm);
	avatarForm.append(avatarHeader);
	avatarForm.append(avatarContainer);
	avatarForm.append(startBtn);
	avatarContainer.append(avatarDisplayContainer);
	avatarContainer.append(avatarSelectionContainer);

	avatarDisplayContainer.append(avatarDisplay);
	avatarSelectionContainer.append(avatarEye, avatarMouth, avatarColor);
	avatarForm.classList.add("move-in");
}

document.addEventListener("DOMContentLoaded", () => {
	init();
});
