import { body, createElement } from "./DOM.js"
import EventBUS from "./EventBUS.js";

export function createLandingScreen() {
    const screen = createElement("div", {}, "landing-screen");
    body.appendChild(screen);

    const login = createElement("button")
    login.innerText = "Login with Spotify"
    login.onclick = async () => {
        const response = await fetch("/auth/login")
        if (response.status === 401) {
            const json = await response.json();
            if (json.error === "No token found. Please login first.") {
                const loginLink = json.url;
                window.open(loginLink, "_blank");
            }
        }
        EventBUS.fireEvent("login", {});
    }
    screen.appendChild(login);
}
export function removeLandingScreen() {
    const screen = body.querySelector(".landing-screen");
    if (screen) {
        screen.remove();
    }
}