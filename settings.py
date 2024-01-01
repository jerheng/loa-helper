import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_API_SECRET = os.getenv("DISCORD_API_TOKEN")

#Get emoji id from \:emojiname: and it'll appear accordingly
emojis = ['<:wed:1190936535231635486>', '<:thu:1190936547328008203>', '<:fri:1190936557885083648>', '<:sat:1190936569457160292>', '<:sun:1190936626424197190>', '<:mon:1190936663103373343>', '<:tue:1190936712701034637>']
headers = ["Names", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon", "Tue"]
emoji_dict = {'<:wed:1190936535231635486>': 'Wed', '<:thu:1190936547328008203>': 'Thu', '<:fri:1190936557885083648>': 'Fri', '<:sat:1190936569457160292>': 'Sat', '<:sun:1190936626424197190>': 'Sun', '<:mon:1190936663103373343>': 'Mon', '<:tue:1190936712701034637>': 'Tue'}
