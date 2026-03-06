import discord
import os
from flask import Flask
from threading import Thread

# --------------------------
# Flask Keep-Alive (optional)
# --------------------------
app = Flask("")

@app.route("/")
def home():
    print("Ping received")
    return "Bot is alive!"

def run_flask():
    # Render provides PORT environment variable automatically
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Start Flask in a separate thread (optional)
Thread(target=run_flask).start()

# --------------------------
# Discord Bot Setup
# --------------------------
TOKEN = os.getenv("TOKEN")  # <-- secure token from Render environment variable

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

client = discord.Client(intents=intents)

# --------------------------
# Channel Mapping
# SOURCE : TARGET
# --------------------------
FORWARD_MAP = {
    1477532587474944053: 1477408829082701904,  # seed
    1477532587474944052: 1478717939036323970,  # gear
    1478441281100189696: 1477409406554734784,  # weather / stocks
}

# --------------------------
# Emoji Settings
# --------------------------
L_EMOJI = "<:L_:1479008795203076096>"  # replace with your emoji ID
W_EMOJI = "<:W_:1479008901520429067>"  # replace with your emoji ID

# --------------------------
# Events
# --------------------------
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    # Debug logs
    print(f"Message from {message.channel.name} by {message.author}: '{message.content}'")
    print(f"Embeds count: {len(message.embeds)}, Attachments count: {len(message.attachments)}")

    # Prevent forwarding own messages
    if message.author == client.user:
        return

    # Only forward from mapped channels
    if message.channel.id not in FORWARD_MAP:
        return

    target = client.get_channel(FORWARD_MAP[message.channel.id])
    if not target:
        print(f"❌ Target channel for {message.channel.name} not found")
        return

    try:
        forwarded_messages = []

        # Forward text
        if message.content:
            sent_msg = await target.send(message.content)
            forwarded_messages.append(sent_msg)

        # Forward attachments
        for attachment in message.attachments:
            file = await attachment.to_file()
            sent_msg = await target.send(file=file)
            forwarded_messages.append(sent_msg)

        # Forward embeds
        for embed in message.embeds:
            sent_msg = await target.send(embed=embed)
            forwarded_messages.append(sent_msg)

        # Add reactions to all forwarded messages
        for f_msg in forwarded_messages:
            try:
                await f_msg.add_reaction(W_EMOJI)
                await f_msg.add_reaction(L_EMOJI)
            except Exception as e:
                print(f"⚠️ Error adding reactions: {e}")

        print(f"📤 Forwarded from {message.channel.name} → {target.name} with reactions")

    except discord.Forbidden:
        print("❌ Missing permissions in target channel")
    except Exception as e:
        print(f"⚠️ Error forwarding message: {e}")

# --------------------------
# Run Bot
# --------------------------
client.run(TOKEN)