# Postgres/pgvector as storage foundation

Swift Bot stores documents and片段 in Postgres with pgvector enabled, even though the MVP still uses lightweight keyword retrieval. We chose this because the product needs a stable local persistence layer now and a low-friction path to future vector retrieval later; swapping from JSON files after real usage would be more disruptive than reserving the vector-capable schema upfront.
