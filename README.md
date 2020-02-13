# WhatsApp log to spotify playlist

This will extract all the spotify links from a WhatsApp chat log and upload them to the
selected spotify playlist ID, avoiding duplicates.

## Installation

```bash
git clone https://github.com/willcl-ark/whatsapp_spotify.git
cd whatsapp_spotify
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Open and edit file `priv.py` and add the required values between the quotation marks:

To get your `client_id` go to your [spotify dashboard](https://developer.spotify.com/dashboard/login) and login. Next click "create client_id" and fill in the form, choosing "desktop app" type. On the second prompt, be sure to select "No" ... I am not making a commercial product.

This will make an "app" in your dashboard. Click the app tile to see your `client_id` and click the green text below client_id to show your `client_secret`. Fill them both in `priv.py`. While you are on this page, click green `Edit Settings` button to edit app settings. In the box marked `redirect URIs` enter: `http://localhost/`

Finally fill your Spotify username in `priv.py`, save the file and exit.

## Chat log and playlist ID

You should probably make a new blank playlist in Spotify App now, or risk danger with an existing one!

Right click the playlist (or control click on OS X) and choose `share > copy Spotify URI`. You will get a string like "spotify:playlist:0Bb0r2yj7JrooH2nxxplgM" where the part after the final colon is the Spotify playlist ID, e.g. `0Bb0r2yj7JrooH2nxxplgM`. Keep this ready for when we run the program.

Also we need the WhatsApp chat log itself. In WhatsApp (on mobile only, desktop does seem to allow it) enter the chat, click at the top to go into "Group Info" then scroll to the bottom and hit "Export Chat". You don't need to include media.

Email the zip file to yourself, unzip the .zip archive and save the .txt file somewhere for later.


## Running

In the `whatsapp_spotify` directory created above, and with the venv activated (`source venv/bin/activate`)! run command:

```bash
python main.py
```

...in the terminal. You will be prompted for the spotify playlist ID and the exact (full!) path to the chat log.

If you are having difficulty with the path, use the terminal to navigate to the directory with the log.txt file in and use command `pwd` (Print Working Directory) to show the exact full path; simply add the log file name including the .txt bit onto the end of it.

Hopefully, now we have great success and it all completes!