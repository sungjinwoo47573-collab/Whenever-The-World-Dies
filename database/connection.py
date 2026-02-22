import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        # Initializes the MongoDB client using the URI from your .env
        self.client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.db = self.client.get_database("jjk_rpg")
        
        # Collection Shortcuts for easy access across all cogs
        self.players = self.db["players"]
        self.clans = self.db["clans"]
        self.items = self.db["items"]
        self.techniques = self.db["techniques"]
        self.skills = self.db["skills"]
        self.skills_library = self.db["skills_library"]
        self.npcs = self.db["npcs"]
        self.codes = self.db["codes"]

    async def ping(self):
        """Verifies if the database connection is active."""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"❌ Database Ping Failed: {e}")
            return False

    def get_io_loop(self):
        return self.client.get_io_loop()

# Create a singleton instance for the entire project
db = Database()
