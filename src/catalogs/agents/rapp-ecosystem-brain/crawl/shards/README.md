# crawl/shards/ — one file per crawl shard (never a shared file)

Each writer writes its own `<shard>.json`. inventory.json (generated) lists all
repos; shards partition them so writers never touch the same file.
