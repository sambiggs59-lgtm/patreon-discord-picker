
import json
import os
import random
import requests
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_URL = (
    "https://sambiggs59-lgtm.github.io/vgcc/"
    "PatreonContent/patreoncontent.json"
)

STATE_FILE = Path("used_links.json")
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# Check UK time
now = datetime.now(ZoneInfo("Europe/London"))

manual_run = os.getenv("MANUAL_RUN", "").lower() == "true"

if not manual_run and (now.weekday() != 6 or now.hour != 9):
    print(f"Skipping run: UK time is {now}")
    raise SystemExit(0)

# Download the latest Patreon content
response = requests.get(DATA_URL, timeout=30)
response.raise_for_status()
items = response.json()

# Remove duplicate links
posts = {}
for item in items:
    link = item.get("patreonLink")
    if link and link.startswith("https://www.patreon.com/"):
        posts[link] = item

posts = list(posts.values())

if not posts:
    raise RuntimeError("No valid Patreon posts found.")

# Load posting history
if STATE_FILE.exists():
    state = json.loads(STATE_FILE.read_text())
else:
    state = {"used": []}

used = set(state.get("used", []))

# Select an unused post
unused = [
    post for post in posts
    if post["patreonLink"] not in used
]

# Start a new cycle when necessary
if not unused:
    print("All posts used. Starting a new cycle.")
    used.clear()
    unused = posts.copy()

chosen = random.choice(unused)

title = chosen.get("title", "Untitled")
series = chosen.get("series", "Unknown")
date = chosen.get("date", "Unknown")
tier = chosen.get("tier", "Unknown")
link = chosen["patreonLink"]

# Prepare Discord message
message = (
    "**This Week's Random Patreon Post**\n\n"
    f"**Title:** {title}\n"
    f"**Series:** {series}\n"
    f"**Date:** {date}\n\n"
    f"**Patreon Tier: @{tier}\n\n and above**"
    f"🔗 {link}"
)

# Send to Discord
discord_response = requests.post(
    WEBHOOK_URL,
    json={"content": message},
    timeout=30
)
discord_response.raise_for_status()

# Save history only after successful posting
used.add(link)

STATE_FILE.write_text(
    json.dumps({"used": sorted(used)}, indent=2)
)

print(f"Successfully posted: {title}")
