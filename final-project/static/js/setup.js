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
    startBtn.textContent = "Start!"

    startBtn.addEventListener("click", function(e) {
        e.preventDefault();
        name = nameInput.value;
        if (1) { // If name is valid - not empty, not too long
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
    let avatar = "";
    const avatarForm = document.createElement("form");

    const avatarHeader = document.createElement("h1");
    avatarHeader.classList.add("avatar-header");
    avatarHeader.textContent = "Create your avatar";

    const avatarInput = document.createElement("input");
    avatarInput.classList.add("name-input");
    avatarInput.placeholder = "Enter your avatar";

    const startBtn = document.createElement("button");
    startBtn.classList.add("start-btn");
    startBtn.textContent = "Play!"

    startBtn.addEventListener("click", function(e) {
        e.preventDefault();
        avatar = avatarInput.value;
        if (1) {}
    });

    formContainer.append(avatarForm);
    avatarForm.append(avatarHeader);
    avatarForm.append(avatarInput);
    avatarForm.append(startBtn);
    avatarForm.classList.add("move-in");
}

document.addEventListener("DOMContentLoaded", () => {
	init();
});