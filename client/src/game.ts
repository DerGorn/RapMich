import { body, createElement } from "./DOM.js"

type SongInfo = {
    uri: string,
    name: string,
    artist: string[],
    album: string,
    release_date: string,
    url: string,
    duration_ms: number,
};

async function playSong(song_info: SongInfo | undefined = undefined): Promise<boolean> {
    let startTime = 0;
    if (song_info?.duration_ms) {
        startTime = Math.floor(Math.random() * song_info.duration_ms / 3);
    }
    const query = song_info ? `?uri=${song_info?.uri}&start_ms=${startTime}` : "";

    const playResponse = await fetch("/api/play" + query, { method: "POST" });

    if (playResponse.status === 401) {
        const playJson = await playResponse.json();
        if (playJson.error === "No token found. Please login first.") {
            const loginLink = playJson.url;
            window.open(loginLink, "_blank");
            return false;
        }
    } else if (playResponse.status !== 204) {
        console.error(playResponse.status, await playResponse.json());
        return false;
    }
    return true;
}

export default function createGameScreen() {
    const random = createElement("button", {}, "playButton");
    let playing = false;
    let paused = false;
    let song_info: SongInfo | undefined = undefined;
    let timer: number | undefined = undefined;
    random.onmousedown = async () => {
        if (!playing) {
            clear_result()
            paused = false;
            const response = await fetch("/api/songinfo/playlist/1CtyLM8ZbtqBs68qL0lijw")
            console.log(response.status);
            if (response.status === 200) {
                song_info = await response.json();
                console.log(song_info);
                if (await playSong(song_info)) {
                    timer = setTimeout(async () => {
                        if ((await fetch("/api/pause", { method: "POST" })).status === 204) {
                            paused = true;
                        }
                    }, 15000);
                }
            } else {
                console.error(response.status, await response.json());
            }
        }
    };
    random.onmouseup = async (e) => {
        if (playing) {
            random.blur()
            e.preventDefault()
            e.stopPropagation()
            timer && clearTimeout(timer)
            let song = song_info || {
                album: "Embers of a Dying World",
                artist: ["Mors Principium Est"],
                name: "Death Is the Beginning",
                release_date: "2017-02-10",
                duration_ms: 20000,
                uri: "spotify:track:6eEoVtxv3rchhu82JkVzNe",
                url: "https://open.spotify.com/track/6eEoVtxv3rchhu82JkVzNe"
            }
            paused && await playSong()
            song && populate_result(song)
        }
        playing = !playing
    }
    const playIcon = createElement("div", {
        style: {
            borderLeft: "100px solid var(--icon-color)",
            borderTop: "50px solid transparent",
            borderBottom: "50px solid transparent",
            opacity: "var(--play-icon)",
            position: "absolute",
            top: "12px",
            left: "12px",
        }
    })
    random.appendChild(playIcon)

    const pauseIcon = createElement("div", {
        style: {
            borderLeft: "28px solid var(--icon-color)",
            borderRight: "28px solid var(--icon-color)",
            width: "24px",
            marginLeft: "8px",
            height: "100px",
            position: "absolute",
            top: "12px",
            left: "12px",
            opacity: "var(--pause-icon)",
        }
    })
    random.appendChild(pauseIcon)
    body.appendChild(random);

    const result = createElement("div", { style: { height: "50%" } }, "result");
    result.appendChild(createElement("div", {}, "resultSacrifice"));
    body.appendChild(result);

    const populate_result = (song_info: SongInfo) => {
        const sacrifice = createElement("div", {}, "resultSacrifice");
        const song = createElement("p");
        song.innerText = song_info.name;
        sacrifice.appendChild(song);

        const artist = createElement("p");
        artist.innerText = song_info.artist.reduce((acc, curr) => acc + ", " + curr);
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
} 
