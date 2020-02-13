"""Parse a WhatsApp Exported chat file for Spotify links and add them to the supplied
playlist ID.
"""


import re
from pathlib import Path

import spotipy

from priv import my_username, client_id, client_secret
from url_regex import URL_REGEX

tt_playlist_id = "0Bb0r2yj7JrooH2nxxplgM"


def chunks(_list: list, n: int):
    """Yield successive n-sized chunks from a list.
    """
    for i in range(0, len(_list), n):
        yield _list[i : i + n]


def extract_from_log_file(log_file_path: str) -> list:
    """Extract all links which start with https://open.spotify.com/track from a WhatsApp
    style chat log.

    N.B This excludes album and playlist links
    """
    # Get the tracks from the log file
    with open(log_file_path, "r", encoding="utf-8") as logfile:
        raw_log = logfile.read()

    log_tracks = [
        link
        for link in re.findall(URL_REGEX, raw_log)
        for link in re.findall(r"^([^?]+)", link)
        if link.startswith("https://open.spotify.com/track")
    ]
    print(f"Got {len(log_tracks)} track IDs from the log file")
    return log_tracks


def get_current_playlist(sp: spotipy.Spotify, playlist_id) -> list:
    """Fetches all the tracks in the supplied playlist ID and returns them as a list of
    URLS.
    """
    offset = 0
    current_playlist_urls = []
    while True:
        response = sp.playlist_tracks(playlist_id, offset=offset)
        if len(response["items"]) == 0:
            break
        offset += len(response["items"])
        current_playlist_urls += [
            item["track"]["external_urls"]["spotify"] for item in response["items"]
        ]
    print(f"{len(current_playlist_urls)} tracks already in the playlist")
    return current_playlist_urls


def main():
    print(f"TT playlist ID: {tt_playlist_id}")
    playlist_id = str(
        input("Enter the spotify playlist ID to add to:\n") or tt_playlist_id
    )
    log_file_path = input(
        "Paste the full path of the WhatsApp log file "
        "(.txt part from extracted zip only):\n"
    )
    while True:
        if Path(log_file_path).is_file() and log_file_path.endswith(".txt"):
            break
        else:
            print(f"Cannot find log file at {log_file_path}")
            log_file_path = input("Please try again:")

    # Get all the https://open.spotify.com/track links from the log
    log_tracks = extract_from_log_file(log_file_path)

    # Setup the spotify token
    token = spotipy.prompt_for_user_token(
        username=my_username,
        scope="playlist-modify-private,playlist-modify-public",
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost/",
    )
    if not token:
        print("Could not authorise token, exiting")
        return

    # Create the spotify object we can use to talk to the API
    sp = spotipy.Spotify(auth=token)
    sp.trace = False

    # Get current playlist contents
    current_playlist_urls = get_current_playlist(sp, playlist_id)

    # Get the diff between the two lists
    diff = [x for x in log_tracks if x not in current_playlist_urls]
    print(f"{len(diff)} new tracks to add")

    # Add the tracks as required
    link_chunks = chunks(diff, 99)
    for chunk in link_chunks:
        sp.user_playlist_add_tracks(my_username, playlist_id, chunk)

    print(f"Added {len(diff)} tracks to playlist {playlist_id}")


if __name__ == "__main__":
    main()
