// setup.js - initializes the game and name + avatar creation
import { connectToServer, getSocket } from "./network.js";
import { initCanvas, setBrushColor, setBrushSize, setTool, clearCanvas, undo } from "./drawing.js";
import { initChatDOM } from "./chat.js";

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

function randomColor() {
    const r = Math.floor(Math.random() * 256);
    const g = Math.floor(Math.random() * 256);
    const b = Math.floor(Math.random() * 256);
    return `rgb(${r}, ${g}, ${b})`;
}

function generateUniqueId() {
	return "id-" + Math.random().toString(36).slice(2, 11);
}

function init() {
    document.body.innerHTML = "";

    const gameHeader = document.createElement("img");
    gameHeader.src = "/static/images/logo.png";
    gameHeader.alt = "drawing game";
    gameHeader.classList.add("game-header");
    document.body.append(gameHeader);

    const formContainer = document.createElement("div");
    formContainer.classList.add("form-container");
    document.body.append(formContainer);

    const form = document.createElement("form");
    formContainer.append(form);
	form.addEventListener("submit", (e) => {
		e.preventDefault();
	});

    // Name Input
    nameInput = document.createElement("input");
    nameInput.classList.add("name-input");
    nameInput.placeholder = "Enter your name";
    form.append(nameInput);

    // Avatar Containers
    const avatarContainer = document.createElement("div");
    avatarContainer.classList.add("avatar-container");
    form.append(avatarContainer);

    const avatarDisplayContainer = document.createElement("div");
    avatarDisplayContainer.classList.add("avatar-display-container");

    const avatarSelectionContainer = document.createElement("div");
    avatarSelectionContainer.classList.add("avatar-selection-container");

    avatarContainer.append(avatarDisplayContainer, avatarSelectionContainer);

    // Avatar images
    const avatarDisplay = document.createElement("img");
    avatarDisplay.classList.add("avatar-display");
    avatarDisplay.src = "static/images/avatar-skeleton.png";

    const eyeMain = document.createElement("img");
    eyeMain.classList.add("eye-main");
    eyeMain.src = "static/images/eyes/eye-avatar-1.png";

    const mouthMain = document.createElement("img");
    mouthMain.classList.add("mouth-main");
    mouthMain.src = "static/images/mouths/mouth-avatar-1.png";

    const colorMain = document.createElement("img");
    colorMain.classList.add("color-main");
    colorMain.src = `static/images/colors/color-avatar-${colors[0]}.png`;

    avatarDisplayContainer.append(avatarDisplay, colorMain, eyeMain, mouthMain);

    // Avatar selectors
    const avatarEye = document.createElement("div");
	avatarEye.classList.add("avatar-eye");
    const eyePreview = document.createElement("img");
    eyePreview.src = "static/images/eyes/eye-preview-1.png";
	eyePreview.classList.add("eye-preview");
    const eyeArrow = document.createElement("button");
    eyeArrow.type = "button";
	eyeArrow.classList.add("eye-arrow");
    eyeArrow.textContent = ">";
    avatarEye.append(eyePreview, eyeArrow);

    const avatarMouth = document.createElement("div");
	avatarMouth.classList.add("avatar-mouth");
    const mouthPreview = document.createElement("img");
    mouthPreview.src = "static/images/mouths/mouth-preview-1.png";
	mouthPreview.classList.add("mouth-preview");
    const mouthArrow = document.createElement("button");
    mouthArrow.type = "button";
	mouthArrow.classList.add("mouth-arrow");
    mouthArrow.textContent = ">";
    avatarMouth.append(mouthPreview, mouthArrow);

    const avatarColor = document.createElement("div");
	avatarColor.classList.add("avatar-color");
    const colorPreview = document.createElement("img");
    colorPreview.src = "static/images/colors/color-preview-white.png";
	colorPreview.classList.add("color-preview");
    const colorArrow = document.createElement("button");
    colorArrow.type = "button";
	colorArrow.classList.add("color-arrow");
    colorArrow.textContent = ">";
    avatarColor.append(colorPreview, colorArrow);

    avatarSelectionContainer.append(avatarEye, avatarMouth, avatarColor);

    // Controllers
    initEyeController(eyeArrow, eyeMain, eyePreview);
    initMouthController(mouthArrow, mouthMain, mouthPreview);
    initColorController(colorArrow, colorMain, colorPreview);

    // Play Button
    const playBtn = document.createElement("button");
    playBtn.classList.add("play-btn");
    playBtn.textContent = "Play!";
    playBtn.type = "button";
    form.append(playBtn);

    playBtn.addEventListener("click", (e) => {
        e.preventDefault();

        const playerData = {
            id: generateUniqueId(),
            name: nameInput.value.trim(),
            avatar: { eye: eyeIdx, mouth: mouthIdx, color: colors[colorIdx] },
        };

        if (!playerData.name) {
            alert("Please enter a name.");
            return;
        }
		initLoadingScreen();

		connectToServer(playerData, (socket) => {
			document.body.innerHTML = "";
			initPlayScreen(socket);
		});
    });
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
	}, 3000);
}

function initPlayScreen(socket) {
	const playArea = document.createElement("div");
	playArea.classList.add("play-area");
	document.body.append(playArea);

	const scoreboard = document.createElement("div");
	scoreboard.classList.add("play-scoreboard");
	playArea.append(scoreboard);

	const drawpad = document.createElement("div");
	drawpad.classList.add("play-drawpad");

	const header = document.createElement("div");
	header.classList.add("play-header");
	playArea.append(header);

	// === TIMER ELEMENT ===
	const timerContainer = document.createElement("div");
	timerContainer.classList.add("timer-container");
	
	// Clock image
	const clockImg = document.createElement("img");
	clockImg.src = "static/images/icons/alarm-clock.svg";
	clockImg.classList.add("timer-clock");

	// Timer text overlay
	const timerText = document.createElement("div");
	timerText.classList.add("timer-text");
	timerText.textContent = ""; // starts empty

	timerContainer.append(clockImg, timerText);
	header.append(timerContainer);

	const promptBanner = document.createElement("div");
	promptBanner.classList.add("prompt-banner");

	// Two H2 elements
	const line1 = document.createElement("h2");
	line1.classList.add("prompt-line1");
	line1.textContent = "";

	const line2 = document.createElement("h2");
	line2.classList.add("prompt-line2");
	line2.textContent = "";

	promptBanner.append(line1, line2);
	header.append(promptBanner);

	const canvas = document.createElement("canvas");
	canvas.classList.add("draw-canvas");

	drawpad.append(canvas);
	playArea.append(drawpad);

	function resizeCanvas() {
		const rect = drawpad.getBoundingClientRect();
		canvas.width = rect.width;
		canvas.height = rect.height;
	}

	resizeCanvas();

	const chat = document.createElement("div");
	chat.classList.add("play-chat");
	playArea.append(chat);

	const drawtools = document.createElement("div");
	drawtools.classList.add("play-drawtools", "hidden");
	document.body.append(drawtools);
	createTools(drawtools);

	initCanvas(canvas, socket);
	initChatDOM(chat);
}

function createTools(drawtools) {
	// Contains brush, eraser, fill bucket
	const leftGroup = document.createElement("div");
	leftGroup.classList.add("tools-left-group");
	drawtools.append(leftGroup);

	// Select Brush
	const brushContainer = document.createElement("div");
	brushContainer.classList.add("brush-container");
	const brushIcon = document.createElement("img");
	brushIcon.classList.add("brush-icon");
	brushIcon.src = "static/images/icons/brush.svg";
	brushIcon.alt = "Brush";
	brushContainer.append(brushIcon);
	leftGroup.append(brushContainer);

	setTool("brush");
	brushIcon.classList.add("selected-tool");

	// Select Eraser
	const eraserContainer = document.createElement("div");
	eraserContainer.classList.add("eraser-container");
	const eraserIcon = document.createElement("img");
	eraserIcon.classList.add("eraser-icon");
	eraserIcon.src = "static/images/icons/eraser.svg";
	eraserIcon.alt = "Eraser";
	eraserContainer.append(eraserIcon);
	leftGroup.append(eraserContainer);

	// Select Fill Bucket
	const fillContainer = document.createElement("div");
	fillContainer.classList.add("fill-container");
	const fillIcon = document.createElement("img");
	fillIcon.classList.add("fill-icon");
	fillIcon.src = "static/images/icons/fill.svg";
	fillIcon.alt = "Fill";
	fillContainer.append(fillIcon);
	leftGroup.append(fillContainer);

	brushIcon.addEventListener("click", () => {
		setTool("brush");

		brushIcon.classList.add("selected-tool");
		eraserIcon.classList.remove("selected-tool");
		fillIcon.classList.remove("selected-tool");
	});

	eraserIcon.addEventListener("click", () => {
		setTool("eraser");

		eraserIcon.classList.add("selected-tool");
		brushIcon.classList.remove("selected-tool");
		fillIcon.classList.remove("selected-tool");
	});

	fillIcon.addEventListener("click", () => {
		setTool("fill");

		fillIcon.classList.add("selected-tool");
		brushIcon.classList.remove("selected-tool");
		eraserIcon.classList.remove("selected-tool");
	});

	// Colors Container
	const colorsContainer = document.createElement("div");
	colorsContainer.classList.add("colors-container");
	drawtools.append(colorsContainer);

	// Color Grid
	const colorGrid = document.createElement("div");
	colorGrid.classList.add("color-grid");
	colorsContainer.append(colorGrid);

	// Current Color
	const currentColor = document.createElement("div");
	currentColor.classList.add("current-color");
	colorsContainer.append(currentColor);
	let defaultPaletteColor = null;

	for (let i = 0; i < 24; i++) {
		const cell = document.createElement("div");

		const color = randomColor();
    	cell.style.background = color;

		if (i === 0) {
			defaultPaletteColor = color;
		}

		cell.addEventListener("click", () => {
			setBrushColor(color);
			currentColor.style.background = color;
		});

		colorGrid.append(cell);
	}

	setBrushColor(defaultPaletteColor);
	currentColor.style.background = defaultPaletteColor;


	// Brush Size Selector
    const brushSizeSelector = document.createElement("div");
    brushSizeSelector.classList.add("brush-size-selector");
    drawtools.append(brushSizeSelector);

	for (let i = 1; i <= 8; i++) {
		const sizeOption = document.createElement("div");
		sizeOption.classList.add("brush-size-option");
		sizeOption.dataset.size = i;
		const img = document.createElement("img");
		img.src = "static/images/dot.png";
		img.classList.add("brush-size-dot");

		img.style.width = `${i * 32}px`;
		img.style.height = `${i * 32}px`;

		sizeOption.append(img);

		const sizeMap = [2, 4, 8, 12, 16, 20, 25, 30];

		sizeOption.addEventListener("click", () => {
			setBrushSize(sizeMap[i - 1]);

			// Remove selected from all
			document.querySelectorAll(".brush-size-option")
				.forEach(option => option.classList.remove("selected"));

			// Highlight clicked
			sizeOption.classList.add("selected");
		});

		brushSizeSelector.append(sizeOption);
		if (i === 1) {
			sizeOption.classList.add("selected");
			setBrushSize(sizeMap[0]);
		}
	}

	// Contains clear canvas and undo buttons
	const rightGroup = document.createElement("div");
	rightGroup.classList.add("tools-right-group");
	drawtools.append(rightGroup);

	// Undo Button
	const undoContainer = document.createElement("div");
	undoContainer.classList.add("undo-container");
	const undoIcon = document.createElement("img");
	undoIcon.classList.add("undo-icon");
	undoIcon.src = "static/images/icons/undo.svg";
	undoIcon.alt = "Undo";
	undoContainer.append(undoIcon);

	undoContainer.addEventListener("click", () => {
		undo();
		const socket = getSocket();
		if (socket) socket.emit("undo");
	});

	// Clear Button
	const clearContainer = document.createElement("div");
	clearContainer.classList.add("clear-container");
	const clearIcon = document.createElement("img");
	clearIcon.classList.add("clear-icon");
	clearIcon.src = "static/images/icons/clear.svg";
	clearIcon.alt = "Clear";
	clearContainer.append(clearIcon);

	clearContainer.addEventListener("click", () => {
		clearCanvas();
		const socket = getSocket();
		if (socket) socket.emit("clear");
	});

	rightGroup.append(undoContainer);
	rightGroup.append(clearContainer);
}

document.addEventListener("DOMContentLoaded", () => {
	init();
	// initPlayScreen();
});
