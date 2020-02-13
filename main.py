"""Parse a WhatsApp Exported chat file for Spotify links and add them to the supplied
spotify playlist ID.
"""

# re is for regex pattern matching
import re

# Path lets us check file paths
from pathlib import Path

# 3rd party spotipy module does the talking to spotify API for us
import spotipy

from priv import my_username, client_id, client_secret

# URL_REGEX has _the_ definitive regex pattern match for extracting urls from strings
from url_regex import URL_REGEX

tt_playlist_id = "0Bb0r2yj7JrooH2nxxplgM"


def chunks(_list: list, n: int):
    """Yield successive n-sized chunks from a list.
    """
    for i in range(0, len(_list), n):
        # 'yield' returns a 'generator' object.
        # Each iteration over it will find a list of length 'n' items until they're all
        # returned
        yield _list[i : i + n]


def extract_from_log_file(log_file_path: str) -> list:
    """Extract all links which start with https://open.spotify.com/track from a WhatsApp
    style chat log.

    N.B This excludes album and playlist links
    """
    # First we open the log file in read mode ("r")
    with open(log_file_path, "r", encoding="utf-8") as logfile:
        # Next read all the lines of it into raw_log
        raw_log = logfile.read()

    # This is the magic list comprehension that extracts all the links!
    log_tracks = [
        link
        # This line will get all web links of all kinds
        for link in re.findall(URL_REGEX, raw_log)
        # This line will chop off some annoying crap on the end
        # (in the log some have ?si=some_random_chars on the end, which meant duplicates
        # got added when you re-ran it.
        # Hint: visit https://regex101.com, choose 'python' on the left and enter the
        # regex below: ^([^?]+)
        # Then enter a test string, e.g.: https://open.spotify.com/track/1CeWWs0F2TVm9nejkxg8U4?si=68k1vytzQsCQ1iI_MFyWtg
        # and watch what the regex will do to it
        for link in re.findall(r"^([^?]+)", link)
        # This line will make sure they are all spotify links
        if link.startswith("https://open.spotify.com/track")
    ]

    # We could have written the above ^ like this:
    # log_tracks = []
    # for links in re.findall(URL_REGEX, raw_log):          <-- filter all hyperlinks
    #     for link in re.findall(r"^([^?]+)", links):       <-- cut the crap off
    #         if link.startswith("https://open.spotify.com/track"):     <-- only spotify
    #             log_tracks.append(link)                   <-- add it to our list

    print(f"Got {len(log_tracks)} track IDs from the log file")
    return log_tracks


def get_current_playlist_state(sp: spotipy.Spotify, playlist_id) -> list:
    """Fetches all the tracks in the supplied playlist ID and returns them as a list of
    URLS.
    """
    # Spotify API doesn't allow us to have everything returned at once (it might be big)
    # So we request it in chunks until we get it all.
    # set the offset to 0 and init an empty list
    offset = 0
    current_playlist_urls = []
    while True:
        # Get the first chunk
        response = sp.playlist_tracks(playlist_id, offset=offset)

        # If the length is zero, we get it all and we can exit the loop
        if len(response["items"]) == 0:
            break

        # Increase the offset (by length we got) so that the next chunk starts in the
        # right place
        offset += len(response["items"])

        # Now we add what we got to the our list.
        # This is another list comprehension to filter out only the "URL" from the mass
        # of data received.
        current_playlist_urls += [
            item["track"]["external_urls"]["spotify"] for item in response["items"]
        ]

        # We could have written the above ^ like this:
        # for item in response["items"]:
        #     current_playlist_urls.append(item["track"]["external_urls"]["spotify"])

    print(f"{len(current_playlist_urls)} tracks already in the playlist")
    return current_playlist_urls


def main():
    # Because I expect to use it for this playlist mainly, have it print out the
    # playlist ID for me in the terminal.
    print(f"TT playlist ID: {tt_playlist_id}")

    # Get some input from the user. Using str(input() or tt_playlist_id) will mean that
    # entering nothing, will use my TT playlist ID by default.
    playlist_id = str(
        input("Enter the spotify playlist ID to add to:\n") or tt_playlist_id
    )

    # Get the log file path
    log_file_path = input(
        "Paste the full path of the WhatsApp log file "
        "(.txt part from extracted zip only):\n"
    )
    # Test that the log file path actually exists so we can ask again for it before
    # failing
    while True:
        if Path(log_file_path).is_file() and log_file_path.endswith(".txt"):
            break
        else:
            print(f"Cannot find log file at {log_file_path}")
            log_file_path = input("Please try again:")

    # Get all the https://open.spotify.com/track links from the log
    log_tracks = extract_from_log_file(log_file_path)

    # Setup the spotify API token
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
    current_playlist_urls = get_current_playlist_state(sp, playlist_id)

    # Get the diff between the two lists, spotify doesn't allow an API call to
    # "avoid duplicates" which seems silly, but whatever.
    diff = [x for x in log_tracks if x not in current_playlist_urls]
    print(f"{len(diff)} new tracks to add")

    # Add the tracks as required. We chunk them in sub-lists of length 99 and keep
    # adding until we're done
    link_chunks = chunks(diff, 99)
    for chunk in link_chunks:
        # This is the API call that actually adds them to spotify. Hint: have Spotify
        # open while you do it to see them being added (very fast!)
        sp.user_playlist_add_tracks(my_username, playlist_id, chunk)

    # Tell the user what we did!
    print(f"Added {len(diff)} tracks to playlist {playlist_id}")


if __name__ == "__main__":
    main()
