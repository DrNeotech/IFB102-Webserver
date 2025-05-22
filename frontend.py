from flask import Flask, request, jsonify
import requests
import numpy as np
from collections import defaultdict, Counter
from itertools import chain
import math
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import re
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
from dotenv import load_dotenv
import os
import base64

app = Flask(__name__)

@app.route('/api/', methods=['POST'])
def render_collage():
    TOKEN = os.getenv("TOKEN")
    SECRET = os.getenv("SECRET")

    params = request.get_json()
    r = requests.post("https://accounts.spotify.com/api/token", data={'grant_type': "client_credentials", 'client_id': TOKEN, 'client_secret': SECRET,})
    header = {'Authorization': f"Bearer {r.json()['access_token']}"}

    playlist_id = re.search(r"\/playlist\/([a-zA-Z0-9]+)", params["playlist"]).group(1)

    image_source = params["image_source"]
    group_by = params["group_by"]

    min_songs = params["minimum"]

    session = FuturesSession()
    s = requests.Session()

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    songRequest = session.get(url, params={"fields":"total"}, headers=header).result()
    playlistLength = songRequest.json()["total"]

    futures = [ session.get(url, params={"limit":50, "offset":i*50, "fields":"items(track(artists(name, id, href), album(name, images))"}, headers=header) for i in range(playlistLength//50+1) ]
    track_list = list(chain.from_iterable([future.result().json()["items"] for future in as_completed(futures)]))

    artist_dict = defaultdict(lambda: {"Count": 0, "Image": []})

    for item in track_list:
        try:
            album_images = item['track']['album']['images'][0]['url']
        except:
            print("Skipping local file")
            continue

        if group_by == "album":
            name = item['track']['album']['name']

        else:
            name = item['track']['artists'][0]['name']

        if image_source == "artist":
            if artist_dict[name]["Image"] == []: 
                artist_img = s.get(item['track']['artists'][0]['href'], params={"fields":"name, images.url"}, headers=header).json()

                try:
                    image_url = artist_img["images"][0]["url"]
                except IndexError:
                    print("Artist has no image, skipping")
                    continue

        else:
            image_url = album_images

        artist_dict[name]["Count"] += 1

        if image_url:
            artist_dict[name]["Image"].append(image_url)

    artist_dict = dict(filter(lambda m: m[1]["Count"] >= int(min_songs), artist_dict.items()))

    artists = dict(sorted(artist_dict.items(), key=lambda x: x[1]["Count"], reverse=True))

    counts = [data["Count"]**2 for data in artists.values()]

    square_width = int(np.ceil(np.sqrt(sum(counts)))) - attempt
    grid = np.zeros([square_width, square_width], dtype=object)

    placements = []

    for pos, val in np.ndenumerate(grid):
        x, y = pos
        if grid[x, y] == 0:
            for artist, data in artists.items():
                size = data["Count"]
                if any(p[0] == artist for p in placements):
                    continue
                if x + size <= square_width and y + size <= square_width:
                    region = grid[x:x + size, y:y + size]
                    if np.all(region == 0): 
                        grid[x:x + size, y:y + size] = artist
                            
                        if image_source == "artist":
                            tile_img = data["Image"][0]

                        else:
                            tile_img = Counter(data["Image"]).most_common(1)[0][0]

                        placements.append((artist, (x, y), size, tile_img))
                        break

    print(f"Filled: {np.count_nonzero(grid)}/{grid.size} ({np.count_nonzero(grid)/grid.size})")
    print(f"Missing Artists: {len(artists)-len(placements)}")

    accuracy = np.count_nonzero(grid)/grid.size

    tile_px = 50

    canvas_px = square_width * tile_px
    canvas = Image.new("RGB", (canvas_px, canvas_px), color=(0, 0, 0))

    for artist, (x, y), size, img_url in placements:
        try:
            response = s.get(img_url)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
            img = img.resize((size * tile_px, size * tile_px), Image.Resampling.LANCZOS)
            canvas.paste(img, (y * tile_px, x * tile_px))
        except Exception as e:
            print(f"Failed to load image for {artist}: {e}")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return jsonify({'image':img_base64})


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
