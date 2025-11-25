# CS 322 MVP Project - Drawing Game

Drawing Game is an online multiplayer drawing and guessing game where one player sketches a word and the others must correctly guess the word being drawn.

Last Updated: 11/24/2025

Author: Song Zhang

Contact: songz@uoregon.edu

## About

This project is intended to be the MVP and final project for CS 322 at the University of Oregon.

This version is built using the concepts taught in the CS 322 course and will use HTML, CSS, Javascript and Javascript in the frontend.
The backend is built using Flask, and saves data using MongoDB. Docker is used to containerize and run the database and frontend/backend.

In this MVP, users will be able to take turns drawing a prompt as other users attempt to guess your prompt.
As a guesser, you will try to guess the drawing before anyone else guesses it. As a drawer, you
are trying to get guessers to type your prompt out as quickly as possible.

Existing versions of this project idea can be played online already, but it's meant to be a minimally
working version to aid in another planned project later on.

The main technical challenges were syncing activity between all the players, ensuring the drawing, buttons, timers, and prompts were all accurate.
AI was used mainly on the frontend to implement a lot of the logic with SocketIO which is relatively new to me.

## Running

To run the project:
1. `cd` into the project directory where `docker-compose.yml` is
2. Run `docker compose up --build -d`
3. This should install all the requirements necessary and run the application accessible at `localhost:5000`
    - If it does not work, check the logs and make sure you have Docker installed and running.
    - This will create a local server accessible by anyone in your network.

To deploy it online, I highly recommend creating an online DB at `https://www.mongodb.com/products/platform/atlas-database`
and creating a .env file with MONGO_URI=[URI HERE]. The backend will automatically detect MONGO_URI. Then, remove the current `return MongoClient...` with the uncommented
`return MongoClient...`.

A deployed version can be found at . . . (not completed yet)

Note: It takes ~30 seconds to start the server up from inactivity.
