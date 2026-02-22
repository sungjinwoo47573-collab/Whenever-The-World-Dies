import json
import os
from datetime import datetime
from database.connection import db

BACKUP_DIR = "./backups"

async def create_backup():
    """Exports major collections to JSON. Fixed for proper database subscripting."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collections = ["players", "clans", "items", "techniques", "codes"]
    backup_results = {}

    for coll_name in collections:
        try:
            # Safely access the collection from the db object
            collection = getattr(db, coll_name)
            cursor = collection.find({})
            data = await cursor.to_list(length=None)
            
            file_path = f"{BACKUP_DIR}/{coll_name}_{timestamp}.json"
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4, default=str)
            
            backup_results[coll_name] = len(data)
        except Exception as e:
            print(f"⚠️ Backup Error on {coll_name}: {e}")

    return timestamp, backup_results

async def restore_from_file(collection_name, file_name):
    """Overwrites a collection with data from a backup file."""
    file_path = os.path.join(BACKUP_DIR, file_name)
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r") as f:
        data = json.load(f)

    if data:
        collection = getattr(db, collection_name)
        await collection.delete_many({})
        await collection.insert_many(data)
        return len(data)
    return 0
    
