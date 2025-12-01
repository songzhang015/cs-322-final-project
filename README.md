# CS 322 MVP Project - Drawing Game

Drawing Game is an online multiplayer drawing and guessing game where one player sketches a word and the others must correctly guess the word being drawn.
This serves to be a MVP to be built upon at a later date.

Last Updated: 12/01/2025

Author: Song Zhang

Contact: songz@uoregon.edu

## About

This project is intended to be the MVP for CS 322 at the University of Oregon.

This version is built using the concepts taught in the CS 322 course and uses HTML, CSS, and Javascript in the frontend.
The backend is built using Flask, and saves data using MongoDB. Docker is used to containerize and run the database and frontend/backend.

The main technical challenges were syncing activity between all the players and ensuring the drawing, buttons, timers, and prompts were all accurate for all players.

This project helped me learn about real-time events and the components that go into a game like this.

- Socket.IO events and their design

- State management for rooms, timers, players, chat

- Server vs. client authority, who knows what and how each component can and cannot interact with others

- Various mechanisms such as point systems, word banks, hint reveal systems

- Challenges with UI and UX design, how to make components look and function well individually and as a whole

AI (OpenAI's ChatGPT 5.1) was used mainly on the frontend to implement a lot of the logic with SocketIO which is relatively new to me.

## Running

To run the project:

1. `cd` into the project directory where `docker-compose.yml` is

2. Run `docker compose up --build -d`

3. This should install all the requirements necessary and run the application accessible locally at `localhost:5000`

    - If it does not work, check the logs and make sure you have Docker installed and running.
    
    - This will create a local server accessible by anyone in your network.

To deploy it online, I highly recommend creating an online DB at `https://www.mongodb.com/products/platform/atlas-database`

A deployed version can be found at `https://cs-322-drawing-game.onrender.com/`

Note: It takes ~30 seconds to start the server up from inactivity.
