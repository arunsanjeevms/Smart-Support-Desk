"""
Export the local MongoDB database in mongodump's format (no MongoDB Tools needed on Windows).

    backend/.venv/Scripts/python.exe deploy/db_export.py <output folder>

Writes <collection>.bson and <collection>.metadata.json for every collection of
the database (including the GridFS files of attachments). On the server it is
loaded with:

    mongorestore --drop --db smart_support_desk <output folder>
"""

import json
import sys
from pathlib import Path

import bson
from bson import json_util
from pymongo import MongoClient

URI = "mongodb://127.0.0.1:27017"
DATABASE = "smart_support_desk"
# Left over from early prototypes; nothing in the code uses them.
SKIP = {"app_settings", "counters", "lookups", "workflow_transitions"}


def main(out: Path) -> None:
    db = MongoClient(URI)[DATABASE]
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for name in sorted(db.list_collection_names()):
        if name in SKIP or name.startswith("system."):
            continue
        collection = db[name]
        count = 0
        with open(out / f"{name}.bson", "wb") as fh:
            for document in collection.find(batch_size=500):
                fh.write(bson.encode(document))
                count += 1
        indexes = [
            {"v": 2, "key": dict(spec["key"]), "name": index_name,
             **{k: v for k, v in spec.items() if k not in ("key", "v", "ns")}}
            for index_name, spec in collection.index_information().items()
        ]
        metadata = {"indexes": indexes, "collectionName": name, "type": "collection"}
        (out / f"{name}.metadata.json").write_text(json_util.dumps(metadata), encoding="utf-8")
        total += count
        print(f"{name:34} {count:6} documents, {len(indexes)} indexes")
    print(f"{total} documents exported to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
