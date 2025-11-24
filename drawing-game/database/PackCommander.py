from database.Connection import Connection
import json
import os

class PackCommander(Connection):
    def __init__(self):
        super().__init__()
        self.seed_default_packs()

    def find_all_packs(self):
        return list(self.packs_collection.find({}, {"_id": 0}))
    
    def find_pack(self, name):
        return self.packs_collection.find_one({"name": name}, {"_id": 0})
    
    def insert_pack(self, pack):
        return self.packs_collection.insert_one(pack)
    
    def delete_pack(self, pack_name):
        return self.packs_collection.delete_one({"name": pack_name})
    
    def add_word(self, pack_name, word):
        return self.packs_collection.update_one(
            {"name": pack_name},
            {"$addToSet": {"words": word}}
        )
    
    def delete_word(self, pack_name, word):
        return self.packs_collection.update_one(
            {"name": pack_name},
            {"$pull": {"words": word}}
        )

    # Seeder
    def seed_default_packs(self):
        if self.packs_collection.count_documents({}) > 0:
            print("packs_collection is not empty, skipping seeding...")
            return

        pack_files = [
            "data/animal_pack.json",
            "data/long_pack.json",
            "data/standard_pack.json"
        ]

        print("Starting seeding process...")

        for file_path in pack_files:
            if not os.path.isfile(file_path):
                print(f"Pack file path {file_path} not found, skipping...")
                continue

            with open(file_path, "r") as f:
                data = json.load(f)

            pack_doc = {
                "name": data.get("name"),
                "words": data.get("words", [])
            }

            self.packs_collection.insert_one(pack_doc)
            print(f"Successfully imported {file_path}.")

        print("Seeding complete.")

