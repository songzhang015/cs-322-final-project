from database.PackCommander import PackCommander

class PackService:
    def __init__(self):
        self.cmd = PackCommander()

    def get_all_packs(self):
        return self.cmd.find_all_packs()

    def create_pack(self, pack_name, words):
        if self.cmd.find_pack(pack_name):
            raise FileExistsError("Pack with this name already exists")
        
        pack_doc = { "name": pack_name, "words": words }
        self.cmd.insert_pack(pack_doc)

        return True
    
    def get_pack(self, pack_name):
        pack = self.cmd.find_pack(pack_name)

        if pack is None:
            raise LookupError("Pack not found")
        
        return pack
    
    def delete_pack(self, pack_name):
        pack = self.cmd.find_pack(pack_name)
        if pack is None:
            raise LookupError("Pack not found")

        self.cmd.delete_pack(pack_name)

        return True
    
    def add_word(self, pack_name, word):
        pack = self.cmd.find_pack(pack_name)
        if pack is None:
            raise LookupError("Pack not found")

        if not word.strip():
            raise ValueError("Invalid word")

        self.cmd.add_word(pack_name, word)

        return True
    
    def delete_word(self, pack_name, word):
        pack = self.cmd.find_pack(pack_name)
        if pack is None:
            raise LookupError("Pack not found")
        
        self.cmd.delete_word(pack_name, word)

        return True
    
pack_service = PackService()