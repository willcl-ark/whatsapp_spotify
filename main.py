"""Parse a WhatsApp Exported chat file for Spotify links and add them to the supplied
spotify playlist ID.
"""

# re is for regex pattern matching
import re

# lets us do stuff with web browsers
import webbrowser

# Path lets us check file paths
from pathlib import Path

# Connect to URLs and get responses
import requests

# does the talking to spotify API for us
import spotipy

from priv import client_id, client_secret, my_username

# URL_REGEX has a regex pattern match for extracting (any?) urls from strings
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


def extract_spotify(raw_log):
    # Because I expect to use it for this playlist mainly, have it print out the
    # playlist ID for me in the terminal.
    print(f"TT playlist ID: {tt_playlist_id}")

    # Get some input from the user. Using str(input() or tt_playlist_id) will mean that
    # entering nothing, will use my TT playlist ID by default.
    playlist_id = str(
        input("Enter the spotify playlist ID to add to:\n") or tt_playlist_id
    )

    # Get all links from the log
    log_tracks = []
    for links in re.findall(URL_REGEX, raw_log):  # filter all hyperlinks
        for link in re.findall(r"^([^?]+)", links):  # cut the crap off for spotify
            if link.startswith("https://open.spotify.com/track"):  # only spotify links
                log_tracks.append(link)  # add it to our list

    print(f"Got {len(log_tracks)} track IDs from the log file")
    print(log_tracks)

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
        for item in response["items"]:
            current_playlist_urls.append(item["track"]["external_urls"]["spotify"])

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


def extract_youtube(raw_log):
    # Get all links from the log
    log_tracks = []
    for link in re.findall(URL_REGEX, raw_log):  # filter all hyperlinks
        if "youtu" in link:  # only youtube, works with youtu.be and youtube.com ;)
            log_tracks.append(link)  # add it to our list

    print(f"Got {len(log_tracks)} track IDs from the log file")
    print(log_tracks)

    # Get the "track_id" part of each link without regex!
    cut_links = []
    for link in log_tracks:
        # This one is not available and was killing us somehow...
        if "O8sWbzGwOv0" in link:
            continue
        if "v=" in link:  # https://www.youtube.com/watch?v=aBcDeFGH
            cut_links.append(link.split("v=")[1])
        if "be/" in link:  # https://youtu.be/aBcDeFGH
            cut_links.append(link.split("be/")[1])

    # Make a "watch_videos?"-style list of links
    video_list = "http://www.youtube.com/watch_videos?video_ids=" + ",".join(cut_links)

    # Connect to youtube and get the short URL link for the list
    response = requests.get(video_list)
    playlist_link = response.url.split("list=")[1]

    # Turn it into a "playlist" by appending the "list" to this style link
    playlist_url = (
        "https://www.youtube.com/playlist?list="
        + playlist_link
        + "&disable_polymer=true"
    )

    # Pop it open in your web browser
    webbrowser.open(playlist_url)
    print("Finished!")
    return


def main():
    service = input("Parse youtube (y) or spotify (s) links?:\n").lower()
    while True:
        if service != ("y" or "s"):
            service = input("Please enter using only 'y' or 's':\n")
        else:
            break

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

    # First we open the log file in read mode ("r")
    with open(log_file_path, "r", encoding="utf-8") as logfile:
        # Next read all the lines of it into raw_log
        raw_log = logfile.read()

    if service == "s":
        extract_spotify(raw_log)
    elif service == "y":
        extract_youtube(raw_log)
    else:
        print(f"Somehow an unknown service choice appeared!?: {service}")


if __name__ == "__main__":
    main()
