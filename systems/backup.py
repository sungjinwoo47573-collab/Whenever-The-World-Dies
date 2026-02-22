import json
import os
from datetime import datetime
from database.connection import db

BACKUP_DIR = "./backups"

async def create_backup():
    """Exports all major collections to JSON files."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collections = ["players", "clans", "items", "techniques", "codes"]
    
    backup_results = {}

    for coll_name in collections:
        cursor = db[coll_name].find({})
        data = await cursor.to_list(length=None)
        
        file_path = f"{BACKUP_DIR}/{coll_name}_{timestamp}.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        
        backup_results[coll_name] = len(data)

    return timestamp, backup_results

async def restore_from_file(collection_name, file_name):
    """Restores a specific collection from a backup file."""
    file_path = f"{BACKUP_DIR}/{file_name}"
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r") as f:
        data = json.load(f)

    if data:
        # Clear current data and insert backup
        await db[collection_name].delete_many({})
        await db[collection_name].insert_many(data)
        return len(data)
    return 0
      
