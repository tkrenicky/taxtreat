from taxtreat.services.importer import import_treaty_json

DB = "taxtreat.db"
JSON_FILE = "data/parsed/switzerland.json"

import_treaty_json(JSON_FILE, DB)

print("Import finished.")
