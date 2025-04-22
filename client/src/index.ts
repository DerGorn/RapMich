import { body, createElement } from "./DOM.js"
// import { Loop } from "./Loop.js";

// Loop.start();
type SongInfo = {
    uri: string,
    name: string,
    artist: string,
    album: string,
    release_date: string,
    url: string,
};

const random = createElement("button", {}, "playButton");
let playing = false;
let song_info: SongInfo | undefined = undefined;
random.onmousedown = async () => {
    if (!playing) {
        clear_result()
        const response = await fetch("http://127.0.0.1:8000/random")
        console.log(response.status);
        if (response.status === 200) {
            song_info = await response.json();
            console.log(song_info);
        } else {
            console.error(await response.json());
        }
    }
};
random.onmouseup = async (e) => {
    if (playing) {
        random.blur()
        e.preventDefault()
        e.stopPropagation()
        let song = song_info || {name: "hello From the other side", artist: "world wor two", release_date: "2025", uri:"", url:"", album:""}
        song && populate_result(song)
    }
    playing = !playing
}
const playIcon = createElement("div", {style: {borderLeft: "100px solid var(--icon-color)",
    borderTop: "50px solid transparent",
    borderBottom: "50px solid transparent",
    opacity: "var(--play-icon)",
    position: "absolute",
    top: "12px",
    left: "12px",
}})
random.appendChild(playIcon)

const pauseIcon = createElement("div", {style: {borderLeft: "28px solid var(--icon-color)",
    borderRight: "28px solid var(--icon-color)",
    width: "24px",
    marginLeft: "8px",
    height: "100px",
    position: "absolute",
    top: "12px",
    left: "12px",
    opacity: "var(--pause-icon)",
}})
random.appendChild(pauseIcon)
body.appendChild(random);

const result = createElement("div", {style: {height: "50%"}}, "result");
result.appendChild(createElement("div", {}, "resultSacrifice"));
body.appendChild(result);

const populate_result = (song_info: SongInfo) => {
    const sacrifice = createElement("div", {}, "resultSacrifice");
    const song = createElement("p");
    song.innerText = song_info.name;
    sacrifice.appendChild(song);

    const artist = createElement("p");
    artist.innerText = song_info.artist;
    sacrifice.appendChild(artist);

    const release = createElement("p");
    release.innerText = song_info.release_date;
    sacrifice.appendChild(release);

    result.children[0].remove();
    result.appendChild(sacrifice)
    result.style.setProperty("--border-color", "black");
}
const clear_result = () => {
    result.children[0].remove();
    result.appendChild(createElement("div", {}, "resultSacrifice"))
    result.style.setProperty("--border-color", "transparent");
}


