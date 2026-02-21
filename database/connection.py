import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load secrets from the root .env file
load_dotenv()

class Database:
    def __init__(self):
        # Pulls the URI from your .env
        self.uri = os.getenv("MONGO_URI")
        if not self.uri:
            raise ValueError("❌ MONGO_URI not found in .env file!")
            
        self.client = AsyncIOMotorClient(self.uri)
        # This creates/connects to a database named 'jjk_rpg_db'
        self.db = self.client["jjk_rpg_db"]

    @property
    def players(self):
        """Access the collection of sorcerer profiles."""
        return self.db["players"]
    
    @property
    def npcs(self):
        """Access the collection of custom NPCs and Bosses."""
        return self.db["npcs"]
    
    @property
    def items(self):
        """Access the collection of weapons and accessories."""
        return self.db["items"]
    
    @property
    def techniques(self):
        """Access the collection of Cursed Techniques."""
        return self.db["techniques"]

# Create a single instance to be imported by other files
db = Database()
