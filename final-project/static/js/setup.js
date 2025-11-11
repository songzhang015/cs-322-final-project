// setup.js - initializes the game and name + avatar creation
import { connectToServer } from "./network.js";
let nameInput;
let eyeIdx = 1;
let mouthIdx = 1;
let colorIdx = 0;
const colors = [
	"white",
	"red",
	"orange",
	"yellow",
	"green",
	"blue",
	"purple",
	"gray",
	"brown",
];

function init() {
	let name = "";

	const gameHeader = document.createElement("img");
	gameHeader.src = "/static/images/logo.png";
	gameHeader.alt = "drawing game";
	gameHeader.classList.add("game-header");

	const formContainer = document.createElement("div");
	formContainer.classList.add("form-container");

	const nameForm = document.createElement("form");

	nameInput = document.createElement("input");
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

function generateUniqueId() {
	return "id-" + Math.random().toString(36).slice(2, 11);
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

	const avatarDisplay = document.createElement("img");
	avatarDisplay.classList.add("avatar-display");
	avatarDisplay.src = "static/images/avatar-skeleton.png";

	const avatarEye = document.createElement("div");
	avatarEye.classList.add("avatar-eye");
	const eyeMain = document.createElement("img");
	eyeMain.classList.add("eye-main");
	eyeMain.src = "static/images/eyes/eye-avatar-1.png";
	const eyePreview = document.createElement("img");
	eyePreview.classList.add("eye-preview");
	eyePreview.src = "static/images/eyes/eye-preview-1.png";
	const eyeArrow = document.createElement("button");
	eyeArrow.classList.add("eye-arrow");
	eyeArrow.textContent = ">";
	avatarEye.append(eyePreview, eyeArrow);

	const avatarMouth = document.createElement("div");
	avatarMouth.classList.add("avatar-mouth");
	const mouthMain = document.createElement("img");
	mouthMain.classList.add("mouth-main");
	mouthMain.src = "static/images/mouths/mouth-avatar-1.png";
	const mouthPreview = document.createElement("img");
	mouthPreview.classList.add("mouth-preview");
	mouthPreview.src = "static/images/mouths/mouth-preview-1.png";
	const mouthArrow = document.createElement("button");
	mouthArrow.classList.add("mouth-arrow");
	mouthArrow.textContent = ">";
	avatarMouth.append(mouthPreview, mouthArrow);

	const avatarColor = document.createElement("div");
	avatarColor.classList.add("avatar-color");
	const colorMain = document.createElement("img");
	colorMain.classList.add("color-main");
	colorMain.src = "static/images/colors/color-avatar-white.png";
	const colorPreview = document.createElement("img");
	colorPreview.classList.add("color-preview");
	colorPreview.src = "static/images/colors/color-preview-white.png";
	const colorArrow = document.createElement("button");
	colorArrow.classList.add("color-arrow");
	colorArrow.textContent = ">";
	avatarColor.append(colorPreview, colorArrow);

	const playBtn = document.createElement("button");
	playBtn.classList.add("play-btn");
	playBtn.textContent = "Play!";

	playBtn.addEventListener("click", function (e) {
		e.preventDefault();
		// Gather player data
		const playerData = {
			id: generateUniqueId(), // simple random string
			name: nameInput.value, // player's name from input
			avatar: {
				eye: eyeIdx, // current selected eye
				mouth: mouthIdx, // current selected mouth
				color: colors[colorIdx], // current selected color
			},
		};

		// Connect to server
		connectToServer(playerData);

		// Initialize loading screen
		initLoadingScreen();
	});

	formContainer.append(avatarForm);
	avatarForm.append(avatarHeader);
	avatarForm.append(avatarContainer);
	avatarForm.append(playBtn);
	avatarContainer.append(avatarDisplayContainer);
	avatarContainer.append(avatarSelectionContainer);

	avatarDisplayContainer.append(avatarDisplay, colorMain, eyeMain, mouthMain);
	avatarSelectionContainer.append(avatarEye, avatarMouth, avatarColor);
	avatarForm.classList.add("move-in");
	initEyeController(eyeArrow, eyeMain, eyePreview);
	initMouthController(mouthArrow, mouthMain, mouthPreview);
	initColorController(colorArrow, colorMain, colorPreview);
}

function initEyeController(arrow, avatarDiv, previewDiv) {
	arrow.addEventListener("click", function (e) {
		e.preventDefault();
		if (eyeIdx === 6) {
			eyeIdx = 1;
		} else {
			eyeIdx += 1;
		}
		previewDiv.src = `static/images/eyes/eye-preview-${eyeIdx}.png`;
		avatarDiv.src = `static/images/eyes/eye-avatar-${eyeIdx}.png`;
	});
}

function initMouthController(arrow, avatarDiv, previewDiv) {
	arrow.addEventListener("click", function (e) {
		e.preventDefault();
		if (mouthIdx === 6) {
			mouthIdx = 1;
		} else {
			mouthIdx += 1;
		}
		previewDiv.src = `static/images/mouths/mouth-preview-${mouthIdx}.png`;
		avatarDiv.src = `static/images/mouths/mouth-avatar-${mouthIdx}.png`;
	});
}

function initColorController(arrow, avatarDiv, previewDiv) {
	// 9 colors, will cycle through color-main-[color] and color-preview-[color]
	// as the file names
	arrow.addEventListener("click", function (e) {
		e.preventDefault();
		if (colorIdx === 8) {
			colorIdx = 0;
		} else {
			colorIdx += 1;
		}
		previewDiv.src = `static/images/colors/color-preview-${colors[colorIdx]}.png`;
		avatarDiv.src = `static/images/colors/color-avatar-${colors[colorIdx]}.png`;
	});
}

function initLoadingScreen() {
	document.body.innerHTML = "";
	let dots = 0;

	const loadingText = document.createElement("p");
	loadingText.classList.add("loading-text");
	loadingText.textContent = "Connecting";
	document.body.append(loadingText);

	const interval = setInterval(() => {
		dots = (dots + 1) % 4;
		loadingText.textContent = "Connecting" + ".".repeat(dots);
	}, 750);

	setTimeout(() => {
		clearInterval(interval);
		loadingText.textContent = "Connected!";
	}, 5000);

	setTimeout(() => {
		document.body.innerHTML = "";
		initPlayScreen();
	}, 6000);
}

function initPlayScreen() {
	const playArea = document.createElement("div");
	playArea.classList.add("play-area");
	document.body.append(playArea);

	const header = document.createElement("div");
	header.classList.add("play-header");
	playArea.append(header);

	const scoreboard = document.createElement("div");
	scoreboard.classList.add("play-scoreboard");
	playArea.append(scoreboard);

	const drawpad = document.createElement("div");
	drawpad.classList.add("play-drawpad");
	playArea.append(drawpad);

	const chat = document.createElement("div");
	chat.classList.add("play-chat");
	playArea.append(chat);
}

document.addEventListener("DOMContentLoaded", () => {
	init();
});
