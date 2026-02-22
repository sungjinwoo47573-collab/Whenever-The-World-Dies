import motor.motor_async_io
from config import MONGO_URI, DATABASE_NAME

# Initialize the Async MongoDB Client
client = motor.motor_async_io.AsyncIOMotorClient(MONGO_URI)

# Connect to the specific database
db = client[DATABASE_NAME]

# Accessing Collections
# These will be imported by other scripts to handle data
players_col = db.players
items_col = db.items
npcs_col = db.npcs
clans_col = db.clans
techniques_col = db.techniques
codes_col = db.codes
quests_col = db.quests

async def check_connection():
    """Verify that the database is reachable."""
    try:
        # The ismaster command is cheap and does not require auth.
        await client.admin.command('ismaster')
        print("--- Cursed Energy Core Connected: MongoDB Linked ---")
    except Exception as e:
        print(f"--- FAILED TO CONNECT TO MONGO: {e} ---")
        
