import argparse
from collections import defaultdict
from datetime import datetime
import os
from pathlib import Path
import random
from typing import List, Tuple

from flask import Flask, render_template
from PIL import Image
from PIL.ImageOps import exif_transpose

app = Flask(__name__)


def move_photos(photos: List[Path], destination: Path, min_size: int = 1080):
    destination.mkdir(exist_ok=True)

    for file in Path(destination).rglob('*'):
        os.remove(file)

    paths = []
    for photo in photos:
        img = Image.open(photo)
        img = exif_transpose(img)
        print(img.size)
        width, height = img.size
        aspect_ratio = width / height

        if width < height:
            new_width = min_size
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = min_size
            new_width = int(new_height * aspect_ratio)

        img = img.resize((new_width, new_height))
        path = destination / photo.name
        img.save(path)
        paths.append(path)

    return paths


def find_photos(folder_path: Path) -> Tuple[int, List[Path]]:
    today = datetime.now()

    photos_by_year = defaultdict(list)

    for file in folder_path.rglob('*'):
        if file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
            creation_time = file.stat().st_mtime
            creation_date = datetime.fromtimestamp(creation_time)

            if creation_date.month == today.month and creation_date.day == today.day and creation_date.year < today.year:
                photos_by_year[creation_date.year].append(file)

    if photos_by_year:
        selected_year = random.choice(list(photos_by_year.keys()))
        return selected_year, sorted(photos_by_year[selected_year], key=lambda x: x.stat().st_mtime)
    else:
        return 0, []


@app.route('/')
def display_photos():
    year, photos = find_photos(Path(app.config['PHOTOS_FOLDER']))
    static_photos = move_photos(photos, Path(app.static_folder) / "photos")
    years_delta = datetime.now().year - year if year != 0 else 0
    return render_template('photos.html', photos=[photo.name for photo in static_photos], total=len(photos), years_delta=years_delta)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LocalPhotosRediscovery')
    parser.add_argument('folder_path', type=str, help='Path to the folder containing photos')
    args = parser.parse_args()

    app.config['PHOTOS_FOLDER'] = args.folder_path
    app.run(debug=True)
