import motor.motor_asyncio
import os
from dotenv import load_dotenv

# Load variables from your .env file
load_dotenv()

class Database:
    def __init__(self):
        # Establish connection using the URI from your .env
        self.client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        
        # Define the database name
        self.db = self.client["jjk_rpg"]
        
        # --- Collection Mapping ---
        # Profiles and Progression
        self.players = self.db["players"]
        self.clans = self.db["clans"]
        
        # Combat & NPCs
        self.npcs = self.db["npcs"]
        self.raids = self.db["raids"]
        
        # Equipment & Techniques
        self.items = self.db["items"]
        self.techniques = self.db["techniques"]
        self.fighting_styles = self.db["fighting_styles"]
        
        # The Core Combat Library (Where !CE/!W/!F moves live)
        self.skills = self.db["skills"]
        self.skills_library = self.db["skills_library"]
        
        # Utility & Configuration
        self.codes = self.db["codes"]
        self.guild_config = self.db["config"]

    async def ping(self):
        """Check if the database connection is alive."""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False

# Initialize the shared database instance
db = Database()
