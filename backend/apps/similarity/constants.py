# Engines that can rank resolved tickets (see engines.py).
SEMANTIC = "semantic"  # Sentence Transformers model - understands meaning
KEYWORD = "keyword"  # TF-IDF word overlap - no model needed

# The title and description together need at least this many characters
# before a search makes sense.
QUERY_MIN_LENGTH = 10

# Scores at or above this are shown as a "strong" match, the rest as "possible".
STRONG_MATCH = 0.6
