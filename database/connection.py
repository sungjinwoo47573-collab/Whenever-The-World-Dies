import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.db = self.client["jjk_rpg"]
        
        # Collections for every feature you listed
        self.players = self.db["players"]
        self.npcs = self.db["npcs"]
        self.clans = self.db["clans"]
        self.items = self.db["items"]
        self.techniques = self.db["techniques"]
        self.fighting_styles = self.db["fighting_styles"]
        self.codes = self.db["codes"]
        self.guild_config = self.db["config"]
        self.raids = self.db["raids"]

db = Database()
