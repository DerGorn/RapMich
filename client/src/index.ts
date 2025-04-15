import { body, createElement } from "./DOM.js"
// import { Loop } from "./Loop.js";

// Loop.start();
const random = createElement("button");
random.innerText = "Play Song";
random.onclick = async () => {
    const response = await fetch("http://127.0.0.1:8000/random")
    console.log(response.status, await response.json());
};

body.appendChild(random);
