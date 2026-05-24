import os
import asyncio
import requests
import discord
from discord import app_commands
from discord.ext import tasks, commands
from groq import Groq

# ─── BIBLE DATA ───────────────────────────────────────────────────────────────

CATEGORY_IMAGES = {
    "pentateuch":  "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=600&q=80",
    "historical":  "https://images.unsplash.com/photo-1552374962-c3b8af6dcea0?w=600&q=80",
    "wisdom":      "https://images.unsplash.com/photo-1456324504439-367cee3b3c32?w=600&q=80",
    "prophecy":    "https://images.unsplash.com/photo-1475274047050-1d0c0975c63e?w=600&q=80",
    "gospel":      "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=600&q=80",
    "acts":        "https://images.unsplash.com/photo-1548407260-da850faa41e3?w=600&q=80",
    "epistle":     "https://images.unsplash.com/photo-1512314889357-e157c22f938d?w=600&q=80",
    "apocalyptic": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=600&q=80",
}

OLD_TESTAMENT = [
    {"name": "Genesis",         "chapters": 50,  "abbr": "genesis",          "category": "pentateuch",  "description": "The book of beginnings — creation, the fall, and God's covenant with Abraham."},
    {"name": "Exodus",          "chapters": 40,  "abbr": "exodus",           "category": "pentateuch",  "description": "God delivers Israel from Egypt and reveals His law through Moses."},
    {"name": "Leviticus",       "chapters": 27,  "abbr": "leviticus",        "category": "pentateuch",  "description": "Laws of holiness, sacrifice, and priestly service for God's people."},
    {"name": "Numbers",         "chapters": 36,  "abbr": "numbers",          "category": "pentateuch",  "description": "Israel's journey through the wilderness toward the Promised Land."},
    {"name": "Deuteronomy",     "chapters": 34,  "abbr": "deuteronomy",      "category": "pentateuch",  "description": "Moses' farewell address and the renewal of God's covenant."},
    {"name": "Joshua",          "chapters": 24,  "abbr": "joshua",           "category": "historical",  "description": "Israel conquers and settles the Promised Land under Joshua's leadership."},
    {"name": "Judges",          "chapters": 21,  "abbr": "judges",           "category": "historical",  "description": "Israel's recurring cycles of sin, oppression, repentance, and deliverance."},
    {"name": "Ruth",            "chapters": 4,   "abbr": "ruth",             "category": "historical",  "description": "A beautiful story of loyalty, love, and God's redemptive grace."},
    {"name": "1 Samuel",        "chapters": 31,  "abbr": "1+samuel",         "category": "historical",  "description": "Israel's transition from judges to kings with Saul and David."},
    {"name": "2 Samuel",        "chapters": 24,  "abbr": "2+samuel",         "category": "historical",  "description": "The reign of King David — his triumphs, failures, and devotion."},
    {"name": "1 Kings",         "chapters": 22,  "abbr": "1+kings",          "category": "historical",  "description": "Solomon's glory and the tragic division of Israel's kingdom."},
    {"name": "2 Kings",         "chapters": 25,  "abbr": "2+kings",          "category": "historical",  "description": "The fall of both Israel and Judah into exile."},
    {"name": "1 Chronicles",    "chapters": 29,  "abbr": "1+chronicles",     "category": "historical",  "description": "David's lineage and his preparations for building the temple."},
    {"name": "2 Chronicles",    "chapters": 36,  "abbr": "2+chronicles",     "category": "historical",  "description": "Solomon's temple and the history of Judah's kings."},
    {"name": "Ezra",            "chapters": 10,  "abbr": "ezra",             "category": "historical",  "description": "The return from Babylonian exile and restoration of worship."},
    {"name": "Nehemiah",        "chapters": 13,  "abbr": "nehemiah",         "category": "historical",  "description": "Rebuilding Jerusalem's walls and sparking spiritual revival."},
    {"name": "Esther",          "chapters": 10,  "abbr": "esther",           "category": "historical",  "description": "God's hidden providence through a courageous Jewish queen."},
    {"name": "Job",             "chapters": 42,  "abbr": "job",              "category": "wisdom",      "description": "Suffering, faith, and an encounter with the sovereign God."},
    {"name": "Psalms",          "chapters": 150, "abbr": "psalms",           "category": "wisdom",      "description": "150 songs and prayers covering every emotion of the human heart."},
    {"name": "Proverbs",        "chapters": 31,  "abbr": "proverbs",         "category": "wisdom",      "description": "Divine wisdom and practical guidance for everyday life."},
    {"name": "Ecclesiastes",    "chapters": 12,  "abbr": "ecclesiastes",     "category": "wisdom",      "description": "The search for meaning and purpose under the sun."},
    {"name": "Song of Solomon", "chapters": 8,   "abbr": "song+of+solomon",  "category": "wisdom",      "description": "A poetic celebration of love, devotion, and commitment."},
    {"name": "Isaiah",          "chapters": 66,  "abbr": "isaiah",           "category": "prophecy",    "description": "Judgment and hope — and the clearest portrait of the coming Messiah."},
    {"name": "Jeremiah",        "chapters": 52,  "abbr": "jeremiah",         "category": "prophecy",    "description": "God's passionate call to repentance before the Babylonian exile."},
    {"name": "Lamentations",    "chapters": 5,   "abbr": "lamentations",     "category": "prophecy",    "description": "Heartfelt mourning over the destruction of Jerusalem."},
    {"name": "Ezekiel",         "chapters": 48,  "abbr": "ezekiel",          "category": "prophecy",    "description": "Dramatic visions of God's glory and Israel's future restoration."},
    {"name": "Daniel",          "chapters": 12,  "abbr": "daniel",           "category": "prophecy",    "description": "Faithfulness in exile and sweeping apocalyptic visions."},
    {"name": "Hosea",           "chapters": 14,  "abbr": "hosea",            "category": "prophecy",    "description": "God's relentless, faithful love for a wayward people."},
    {"name": "Joel",            "chapters": 3,   "abbr": "joel",             "category": "prophecy",    "description": "The Day of the Lord and the promise of His Spirit poured out."},
    {"name": "Amos",            "chapters": 9,   "abbr": "amos",             "category": "prophecy",    "description": "A call to justice and righteousness for the oppressed."},
    {"name": "Obadiah",         "chapters": 1,   "abbr": "obadiah",          "category": "prophecy",    "description": "God's judgment against the nation of Edom."},
    {"name": "Jonah",           "chapters": 4,   "abbr": "jonah",            "category": "prophecy",    "description": "God's mercy and compassion extends beyond Israel to all nations."},
    {"name": "Micah",           "chapters": 7,   "abbr": "micah",            "category": "prophecy",    "description": "Act justly, love mercy, and walk humbly with your God."},
    {"name": "Nahum",           "chapters": 3,   "abbr": "nahum",            "category": "prophecy",    "description": "The fall of mighty Nineveh and God's justice over the nations."},
    {"name": "Habakkuk",        "chapters": 3,   "abbr": "habakkuk",         "category": "prophecy",    "description": "Wrestling honestly with God in a time of injustice and silence."},
    {"name": "Zephaniah",       "chapters": 3,   "abbr": "zephaniah",        "category": "prophecy",    "description": "Warning of coming judgment and the promise of joyful restoration."},
    {"name": "Haggai",          "chapters": 2,   "abbr": "haggai",           "category": "prophecy",    "description": "Rebuilding the temple and restoring God's priority in daily life."},
    {"name": "Zechariah",       "chapters": 14,  "abbr": "zechariah",        "category": "prophecy",    "description": "Visions of Israel's restoration and the coming of the King."},
    {"name": "Malachi",         "chapters": 4,   "abbr": "malachi",          "category": "prophecy",    "description": "God's final word before 400 years of silence — and Messiah's coming."},
]

NEW_TESTAMENT = [
    {"name": "Matthew",          "chapters": 28, "abbr": "matthew",          "category": "gospel",      "description": "Jesus as the promised Messiah and rightful King of Israel."},
    {"name": "Mark",             "chapters": 16, "abbr": "mark",             "category": "gospel",      "description": "Jesus as the powerful, action-driven Servant of God."},
    {"name": "Luke",             "chapters": 24, "abbr": "luke",             "category": "gospel",      "description": "Jesus as the compassionate Savior who came for all people."},
    {"name": "John",             "chapters": 21, "abbr": "john",             "category": "gospel",      "description": "Jesus as the eternal Son of God and the Light of the world."},
    {"name": "Acts",             "chapters": 28, "abbr": "acts",             "category": "acts",        "description": "The birth and explosive spread of the early church by the Spirit."},
    {"name": "Romans",           "chapters": 16, "abbr": "romans",           "category": "epistle",     "description": "The gospel of God's grace and righteousness by faith alone."},
    {"name": "1 Corinthians",    "chapters": 16, "abbr": "1+corinthians",    "category": "epistle",     "description": "Practical guidance on Christian living, unity, and spiritual gifts."},
    {"name": "2 Corinthians",    "chapters": 13, "abbr": "2+corinthians",    "category": "epistle",     "description": "Paul's defense of his ministry and the call to radical generosity."},
    {"name": "Galatians",        "chapters": 6,  "abbr": "galatians",        "category": "epistle",     "description": "Freedom from the law through faith in Jesus Christ alone."},
    {"name": "Ephesians",        "chapters": 6,  "abbr": "ephesians",        "category": "epistle",     "description": "The church as the body of Christ and the armor of God."},
    {"name": "Philippians",      "chapters": 4,  "abbr": "philippians",      "category": "epistle",     "description": "Joy and contentment in Christ regardless of circumstances."},
    {"name": "Colossians",       "chapters": 4,  "abbr": "colossians",       "category": "epistle",     "description": "Christ's absolute supremacy over all creation and all things."},
    {"name": "1 Thessalonians",  "chapters": 5,  "abbr": "1+thessalonians",  "category": "epistle",     "description": "Encouragement to live faithfully in light of Christ's return."},
    {"name": "2 Thessalonians",  "chapters": 3,  "abbr": "2+thessalonians",  "category": "epistle",     "description": "Clarity and comfort regarding the Day of the Lord."},
    {"name": "1 Timothy",        "chapters": 6,  "abbr": "1+timothy",        "category": "epistle",     "description": "Paul's instructions for healthy church leadership and doctrine."},
    {"name": "2 Timothy",        "chapters": 4,  "abbr": "2+timothy",        "category": "epistle",     "description": "Paul's final charge to Timothy — preach the Word faithfully."},
    {"name": "Titus",            "chapters": 3,  "abbr": "titus",            "category": "epistle",     "description": "Sound doctrine and godly living in the local church."},
    {"name": "Philemon",         "chapters": 1,  "abbr": "philemon",         "category": "epistle",     "description": "A personal plea for forgiveness, grace, and restoration."},
    {"name": "Hebrews",          "chapters": 13, "abbr": "hebrews",          "category": "epistle",     "description": "Jesus as the fulfillment and completion of the entire Old Testament."},
    {"name": "James",            "chapters": 5,  "abbr": "james",            "category": "epistle",     "description": "Genuine faith always produces visible, practical good works."},
    {"name": "1 Peter",          "chapters": 5,  "abbr": "1+peter",          "category": "epistle",     "description": "Living with hope and holiness while enduring suffering."},
    {"name": "2 Peter",          "chapters": 3,  "abbr": "2+peter",          "category": "epistle",     "description": "Guard the truth of the gospel against dangerous false teachers."},
    {"name": "1 John",           "chapters": 5,  "abbr": "1+john",           "category": "epistle",     "description": "God is love — walk in His light, truth, and love."},
    {"name": "2 John",           "chapters": 1,  "abbr": "2+john",           "category": "epistle",     "description": "Walking in truth and love within the community of believers."},
    {"name": "3 John",           "chapters": 1,  "abbr": "3+john",           "category": "epistle",     "description": "Commending faithful hospitality and partnership in the truth."},
    {"name": "Jude",             "chapters": 1,  "abbr": "jude",             "category": "epistle",     "description": "Contend earnestly for the faith against false teaching."},
    {"name": "Revelation",       "chapters": 22, "abbr": "revelation",       "category": "apocalyptic", "description": "The final and glorious victory of Christ and the new creation."},
]

BIBLE_BOOKS = {"old_testament": OLD_TESTAMENT, "new_testament": NEW_TESTAMENT}

FEATURED_VERSES = [
    {"ref": "John 3:16",       "abbr": "john",       "chapter": 3,  "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."},
    {"ref": "Psalm 23:1",      "abbr": "psalms",     "chapter": 23, "text": "The Lord is my shepherd; I shall not want."},
    {"ref": "Jeremiah 29:11",  "abbr": "jeremiah",   "chapter": 29, "text": "For I know the plans I have for you, saith the Lord, plans for welfare and not for evil, to give you a future and a hope."},
    {"ref": "Philippians 4:13","abbr": "philippians","chapter": 4,  "text": "I can do all things through Christ which strengtheneth me."},
    {"ref": "Isaiah 40:31",    "abbr": "isaiah",     "chapter": 40, "text": "But they that wait upon the Lord shall renew their strength; they shall mount up with wings as eagles."},
    {"ref": "Romans 8:28",     "abbr": "romans",     "chapter": 8,  "text": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose."},
]

# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def fetch_formatted_verse():
    try:
        response = requests.get("https://bible-api.com/?random=verse", timeout=5)
        if response.status_code == 200:
            data = response.json()
            reference = data.get("reference", "Unknown Reference")
            text = data.get("text", "").strip()
            gif_url = "https://tenor.com/view/jesus-heart-sacred-heart-of-jesus-god-gif-12734203"
            return (
                f"|| @everyone ||\n\n"
                f"** Bible Verse For Today **\n"
                f"📖 *{reference}*\n\n"
                f"\"{text}\"\n\n"
                f"{gif_url}"
            )
    except Exception as e:
        print(f"Error fetching verse from API: {e}")
    return None

def ask_jesus_ai(user_question):
    system_prompt = (
        "You are a helpful, gentle, and faithful Bible scholar bot. "
        "Your task is to answer the user's question, but you MUST strictly tie your response back to Jesus Christ, "
        "His teachings, His life, His sacrifice, or love. If the user asks something completely unrelated to faith or Jesus, "
        "politely guide the topic back to Jesus."
    )
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return "⚠️ Configuration Error: The Groq API Key was not found in the environment setup."
            
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return "⚠️ Sorry, I'm having trouble connecting to my study scrolls right now. Please try again in a moment!"

# ─── DISCORD BOT CLIENT ───────────────────────────────────────────────────────

class BibleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.target_channel_id = None

    async def setup_hook(self):
        self.send_bible_verse.start()

    @tasks.loop(hours=5)
    async def send_bible_verse(self):
        if not self.target_channel_id:
            return
        channel = self.get_channel(self.target_channel_id)
        if channel:
            verse_message = fetch_formatted_verse()
            if verse_message:
                try:
                    await channel.send(verse_message)
                    print(f"Interval verse successfully sent to channel {self.target_channel_id}")
                except Exception as e:
                    print(f"Failed to auto-send verse to channel: {e}")
        else:
            print(f"Target channel {self.target_channel_id} not found or inaccessible.")

    @send_bible_verse.before_loop
    async def before_send_bible_verse(self):
        await self.wait_until_ready()

bot = BibleBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} slash command(s) globally.")
    except Exception as e:
        print(f"Failed to sync global commands: {e}")

# ─── INTERACTION COMMANDS ────────────────────────────────────────────────────

@bot.tree.command(name="set-bible-verse", description="Set the channel where Bible verses will be sent every 5 hours.")
@app_commands.describe(channel="The text channel you want the bot to post verses in.")
@app_commands.checks.has_permissions(manage_channels=True)
async def set_bible_verse(interaction: discord.Interaction, channel: discord.TextChannel):
    bot.target_channel_id = channel.id
    await interaction.response.send_message(
        f"✅ Success! I have set the channel to {channel.mention}. Sending the first verse now...",
        ephemeral=True
    )
    
    initial_verse = fetch_formatted_verse()
    if initial_verse:
        try:
            await channel.send(initial_verse)
            print(f"Initial setup verse sent to channel {channel.id}")
        except discord.Forbidden:
            print(f"Permission error: Bot cannot write in channel {channel.id}")
    else:
        await channel.send("⚠️ Bot configured, but failed to fetch the initial verse from the API. It will try again in 5 hours.")

@bot.tree.command(name="ask-bible-bot", description="Ask the bot a question! The response will focus on Jesus Christ.")
@app_commands.describe(message="What would you like to ask or discuss about Jesus?")
async def ask_bible_bot(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    ai_response = ask_jesus_ai(message)
    
    if len(ai_response) > 1950:
        ai_response = ai_response[:1950] + "..."
        
    formatted_reply = f"**🙏 Question:** {message}\n\n{ai_response}"
    await interaction.followup.send(formatted_reply)

# ─── GLOBAL COMMAND ERROR HANDLING ───────────────────────────────────────────

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ You do not have permission to use this command. You need the **Manage Channels** permission.",
                ephemeral=True
            )
    else:
        print(f"Application command runtime exception: {error}")

# ─── KEEPALIVE ENGINE ENTRYPOINT ──────────────────────────────────────────────

async def keep_alive_runner():
    """Maintains a lightweight async process loop to prevent container sleep."""
    print("Keepalive service initialized.")
    while True:
        await asyncio.sleep(3600)  # Heartbeat loop checks in every hour

async def main():
    # This checks for BOTH names automatically so it never fails!
    token = os.environ.get('TOKEN') or os.environ.get('DISCORD_TOKEN')
    
    if not token:
        print("CRITICAL ERROR: Neither 'TOKEN' nor 'DISCORD_TOKEN' was found in the environment variables.")
        return

    print("Token found! Attempting to connect to Discord...")
    # Start the Discord bot runtime
    asyncio.create_task(bot.start(token))
    
    # Run the keepalive loop on the primary thread to lock the environment open
    await keep_alive_runner()


    # Start the Discord bot runtime
    asyncio.create_task(bot.start(token))
    
    # Run the keepalive loop on the primary thread to lock the environment open
    await keep_alive_runner()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Service terminated by user application break.")
