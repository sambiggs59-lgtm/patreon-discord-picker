import json
import os
import random
import requests

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Patreon content source
BASE_URL = (
    "https://sambiggs59-lgtm.github.io/vgcc/"
    "PatreonContent/"
)

IMAGE_BASE_URL = "https://sambiggs59-lgtm.github.io/vgcc/"

DATA_FILES = [
    "patreonContent_cvg.json",
    "patreonContent_offTopic.json",
    "patreonContent_we3.json",
    "patreonContent_acceptableInThe90s.json",
]

# Files and configuration
STATE_FILE = Path("used_links.json")
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# Check UK time
now = datetime.now(ZoneInfo("Europe/London"))

manual_run = os.getenv("MANUAL_RUN", "").lower() == "true"

if not manual_run and (now.weekday() != 6 or now.hour != 9):
    print(f"Skipping run: UK time is {now}")
    raise SystemExit(0)


def load_patreon_posts():
    """Download and combine the Patreon content files."""

    posts = {}

    for filename in DATA_FILES:
        url = BASE_URL + filename

        print(f"Downloading {filename}...")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        items = response.json()

        if not isinstance(items, list):
            raise ValueError(
                f"Unexpected JSON format in {filename}"
            )

        for item in items:
            if not isinstance(item, dict):
                continue

            link = item.get("patreonLink")

            if (
                isinstance(link, str)
                and link.startswith("https://www.patreon.com/")
            ):
                posts[link] = item

        print(f"Loaded {filename}")

    return list(posts.values())


# Download all Patreon posts
posts = load_patreon_posts()

if not posts:
    raise RuntimeError("No valid Patreon posts found.")

print(f"Total unique Patreon posts: {len(posts)}")


# Load posting history
if STATE_FILE.exists():
    state = json.loads(STATE_FILE.read_text())
else:
    state = {"used": []}

used = set(state.get("used", []))


# Find posts that haven't been shared
unused = [
    post for post in posts
    if post["patreonLink"] not in used
]


# Start a new cycle if every post has been shared
if not unused:
    print("All posts used. Starting a new cycle.")
    used.clear()
    unused = posts.copy()


# Pick a random post
chosen = random.choice(unused)

title = chosen.get("title") or "Untitled"
series = chosen.get("series") or "Unknown"
date = chosen.get("date") or "Unknown"
tier = chosen.get("tier")
link = chosen["patreonLink"]

audio = chosen.get("audioLink")
video = chosen.get("videoLink")

# Build image URL from titleImage field
title_image = chosen.get("titleImage")

image_url = None

if isinstance(title_image, str) and title_image:
    image_url = IMAGE_BASE_URL + title_image.lstrip("/")


# Build Discord embed

fields = [
    {
        "name": "**Title:**",
        "value": title,
        "inline": False,
    },
    {
        "name": "**Series:**",
        "value": series,
        "inline": True,
    },
    {
        "name": "**Date:**",
        "value": date,
        "inline": True,
    },
]

if tier:
    fields.append(
        {
            "name": "**Patreon Tier:**",
            "value": f"{tier} and above",
            "inline": True,
        }
    )

if audio:
    fields.append(
        {
            "name": "🎧 Audio",
            "value": audio,
            "inline": False,
        }
    )

if video:
    fields.append(
        {
            "name": "🎬 Video",
            "value": video,
            "inline": False,
        }
    )

embed = {
    "title": "This Week's Random Patreon Post",
    "url": link,
    "color":  F89915,  
    "fields": fields,
    "footer": {
        "text": "VGCC Patreon Archive"
    },
    "timestamp": datetime.utcnow().isoformat() + "Z",
}

# Add title image from JSON
if image_url:
    embed["image"] = {
        "url": image_url
    }

# Send to Discord
discord_response = requests.post(
    WEBHOOK_URL,
    json={
        "username": "Weekly Patreon Picker",
        "embeds": [embed],
    },
    timeout=30,
)

discord_response.raise_for_status()


# Save history after successful posting
used.add(link)

STATE_FILE.write_text(
    json.dumps({"used": sorted(used)}, indent=2)
)

print(f"Successfully posted: {title}")

