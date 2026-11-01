# patreon-discord-picker
Automatically posts a random Patreon link to Discord every week


if tier:
    message += f"**Patreon Tier:** {tier} and above\n"

message += f"\n🔗 **Patreon:** {link}"

if audio:
    message += f"\n🎧 **Audio:** {audio}"

if video:
    message += f"\n🎬 **Video:** {video}"
