import EventBUS from "./EventBUS.js";

const FPSTARGET = 30;

let end = false;
let lastRender = 0;
/**
 * Main loop to continously update the application. It uses window.requestAnimationFrame to
 * sync the updates with the browsers frame rendering. By using requestAnimationFrame a smooth
 * experience can be guaranteed without any stutters
 * @param time time since application start, supplied by window.requestAnimationFrame
 */
const loop = (time: number) => {
  const delta = time - lastRender;
  if (delta >= 1000 / FPSTARGET) {
    update(delta);
    lastRender = time;
  }
  if (!end) window.requestAnimationFrame(loop);
};

const update = (delta: number) => {
  EventBUS.fireEvent("loop", { delta });
};

/**
 * Indicates a fresh reload of the site. Used to setup the togglePlay Event listener on the loop
 */
let firststart = true;
/**
 * Main Loop controller.
 */
const Loop = {
  start: async () => {
    if (Loop.isRunning()) return;
    end = false;
    lastRender = 0;
    window.requestAnimationFrame(loop);
    EventBUS.fireEvent("togglePlay", { play: true });
    if (firststart) {
      firststart = false;
      EventBUS.registerEventListener("requestTogglePlay", {}, (e) => {
        if (e.play) Loop.start();
        else Loop.pause();
      });
    }
  },
  pause: () => {
    if (!Loop.isRunning()) return;
    end = true;
    EventBUS.fireEvent("togglePlay", { play: false });
  },
  isRunning: () => !end,
};

export { Loop };
