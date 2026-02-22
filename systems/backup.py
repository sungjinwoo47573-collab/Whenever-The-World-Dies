import json
import os
from database.connection import db

BACKUP_DIR = "./backups"

async def restore_from_file(collection_name, file_name):
    """Overwrites a collection with data from a backup file."""
    file_path = f"{BACKUP_DIR}/{file_name}"
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r") as f:
        data = json.load(f)

    if data:
        # Warning: This wipes the current collection before inserting backup
        collection = getattr(db, collection_name)
        await collection.delete_many({})
        await collection.insert_many(data)
        return len(data)
    return 0

def delete_backup_file(file_name):
    """Permanently deletes a backup file from the server."""
    file_path = f"{BACKUP_DIR}/{file_name}"
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
    
