import json
import os
from datetime import datetime
from database.connection import db

BACKUP_DIR = "./backups"

async def create_backup():
    """Exports major collections to JSON. Fixed for Motor subscripting."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collections = ["players", "clans", "items", "techniques", "codes"]
    backup_results = {}

    # Access the raw database object from the connection
    database = db.get_io_loop().run_until_complete(db.client.get_database()) if hasattr(db, 'client') else db

    for coll_name in collections:
        # FIX: Ensure we are subscripting the database object, not the wrapper
        try:
            cursor = db[coll_name].find({})
            data = await cursor.to_list(length=None)
            
            file_path = f"{BACKUP_DIR}/{coll_name}_{timestamp}.json"
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4, default=str)
            
            backup_results[coll_name] = len(data)
        except Exception as e:
            print(f"Backup Error on {coll_name}: {e}")

    return timestamp, backup_results
    
