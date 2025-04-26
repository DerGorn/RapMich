import { createLandingScreen, removeLandingScreen } from "./landing.js";
import EventBUS from "./EventBUS.js";
import createGameScreen from "./game.js";
// import { Loop } from "./Loop.js";

// Loop.start();
createLandingScreen();
EventBUS.registerEventListener("login", {}, async () => {
    removeLandingScreen();
    createGameScreen();
})