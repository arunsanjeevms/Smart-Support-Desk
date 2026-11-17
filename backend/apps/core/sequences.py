from django.db import connection
from pymongo import ReturnDocument

COUNTERS_COLLECTION = "core_counters"


def next_sequence(name: str, start: int = 1) -> int:
    """
    Return the next number of a named, gap-free counter.

    Uses MongoDB's atomic ``findOneAndUpdate`` + ``$inc`` so two requests can
    never receive the same number, even without multi-document transactions.
    """
    collection = connection.database[COUNTERS_COLLECTION]
    doc = collection.find_one_and_update(
        {"_id": name},
        [{"$set": {"value": {"$add": [{"$ifNull": ["$value", start - 1]}, 1]}}}],
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["value"])
