---
layout: post
title: "File Sharding: How to Host Unlimited Files on GitHub for Free"
date: 2026-03-29
tags: [file-sharding, github, streaming, tutorial]
---

GitHub has a 50MB file size limit. This is reasonable for source code. It is less reasonable when you want to host a 179MB audiobook, a 500MB dataset, or a 2GB disk image in a git repository and serve it over the web for free.

We solved this with a 332-line Python script that splits any file into 49MB chunks, produces a manifest with SHA-256 integrity hashes, and reassembles the original file client-side. The pattern works for anything: audio, video, model weights, databases, disk images.

## The problem

We had a 3-hour, 42-minute audiobook -- 179,405,403 bytes of M4A audio. We wanted to serve it directly from GitHub Pages with a browser-based player. GitHub rejects files over 50MB on push. GitHub LFS exists but costs money after the free tier and requires authentication for reads. We wanted zero-cost, zero-auth, CDN-backed hosting.

## The solution: shard and manifest

Split the file into chunks that fit under the limit. Store a manifest that records the size and cryptographic hash of each chunk. Reassemble client-side.

```
179MB audiobook
  -> shard-000.bin (49MB)
  -> shard-001.bin (49MB)
  -> shard-002.bin (49MB)
  -> shard-003.bin (32MB)
  -> manifest.json  (1KB)
```

Each chunk is under 49MB -- safely below the 50MB limit with room for git overhead. The manifest records everything needed to put the file back together:

```json
{
  "original_name": "audiobook.m4a",
  "content_type": "audio/mp4a-latm",
  "total_size": 179405403,
  "shard_size": 49000000,
  "sha256": "1870e190fa38e34840ff550666b1448ffae49df4...",
  "shards": [
    {
      "file": "audiobook-000.bin",
      "size": 49000000,
      "sha256": "50da227e89f34a0e33946d09270ba7b4f9c03f70..."
    },
    {
      "file": "audiobook-001.bin",
      "size": 49000000,
      "sha256": "2d7a93db15738b6a044c47ba76cc99959b5155d5..."
    },
    {
      "file": "audiobook-002.bin",
      "size": 49000000,
      "sha256": "5cb2d3a68dee8ebace024931eb3271618c1094e9..."
    },
    {
      "file": "audiobook-003.bin",
      "size": 32405403,
      "sha256": "d16b232020b4a16c6f358202e1a58b09c0962979..."
    }
  ],
  "base_url": "https://raw.githubusercontent.com/your-org/your-repo/main/media/shards/",
  "created_at": "2026-03-29T03:15:44Z"
}
```

## The split algorithm

The splitting logic is intentionally simple:

```python
SHARD_SIZE = 49_000_000  # 49 MB

def split(file_path, output_dir=None):
    src = Path(file_path).resolve()
    total_size = src.stat().st_size
    out = Path(output_dir) if output_dir else src.parent / "shards"
    out.mkdir(parents=True, exist_ok=True)

    shards = []
    whole_hash = hashlib.sha256()
    shard_index = 0

    with open(src, "rb") as f:
        while True:
            data = f.read(SHARD_SIZE)
            if not data:
                break
            whole_hash.update(data)

            shard_name = f"{src.stem}-{shard_index:03d}.bin"
            shard_path = out / shard_name
            with open(shard_path, "wb") as sf:
                sf.write(data)

            shards.append({
                "file": shard_name,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
            shard_index += 1

    # Write manifest with whole-file hash
    manifest = {
        "original_name": src.name,
        "content_type": guess_content_type(src),
        "total_size": total_size,
        "sha256": whole_hash.hexdigest(),
        "shards": shards,
    }
    # ... write to JSON
```

Read 49MB. Write a chunk. Hash it. Repeat until EOF. Compute the whole-file hash as you go. Write the manifest. Done.

## The reassembly (client-side)

In the browser, reassembly uses the Fetch API and Blob:

```javascript
async function reassemble(manifestUrl) {
  const manifest = await fetch(manifestUrl).then(r => r.json());
  const chunks = [];

  for (const shard of manifest.shards) {
    const url = manifest.base_url + shard.file;
    const response = await fetch(url);
    const blob = await response.blob();
    chunks.push(blob);
  }

  const assembled = new Blob(chunks, { type: manifest.content_type });
  return URL.createObjectURL(assembled);
}
```

Fetch each chunk sequentially (or in parallel for speed). Concatenate the Blobs. Create an object URL. Hand it to an `<audio>` or `<video>` element. The browser handles the rest.

For our audiobook player, we stream the chunks progressively -- the player starts as soon as the first chunk arrives while the remaining chunks download in the background.

## Integrity verification

Every shard has a SHA-256 hash. The whole file has a SHA-256 hash. The join operation verifies both:

```python
def join(manifest_path, output_file=None):
    manifest = json.load(open(manifest_path))
    whole_hash = hashlib.sha256()

    with open(dest, "wb") as out:
        for shard in manifest["shards"]:
            data = (shard_dir / shard["file"]).read_bytes()

            # Verify shard hash
            actual = hashlib.sha256(data).hexdigest()
            if actual != shard["sha256"]:
                raise ValueError(f"Hash mismatch: {shard['file']}")

            # Verify shard size
            if len(data) != shard["size"]:
                raise ValueError(f"Size mismatch: {shard['file']}")

            whole_hash.update(data)
            out.write(data)

    # Verify whole-file hash
    if whole_hash.hexdigest() != manifest["sha256"]:
        raise ValueError("Whole-file hash mismatch")
```

If any byte changes in any chunk -- corruption, truncation, tampering -- the hash check catches it. The verification is end-to-end: individual chunk integrity AND reassembled file integrity.

## The CLI

Three commands handle everything:

```bash
# Split a file into shards
python3 scripts/shard.py split audiobook.m4a --output media/shards/

# Verify all shards match their manifest
python3 scripts/shard.py verify media/shards/audiobook.manifest.json

# Reassemble shards back into the original file
python3 scripts/shard.py join media/shards/audiobook.manifest.json --output restored.m4a
```

## What this works for

**Audio.** I sharded a 179MB audiobook into 4 chunks and stream it in the browser. The player loads the complete 3h42m recording from GitHub's CDN, with no auth and no LFS bill.

**Video.** A 1GB MP4 becomes 21 shards. Reassemble client-side into a Blob URL. Feed it to a `<video>` element.

**Model weights.** ML models are often 100MB-10GB. Shard them, commit the shards, serve the manifest. The client reassembles and loads into WebAssembly or ONNX.js.

**Databases.** SQLite files can be sharded and reassembled in the browser using sql.js. Your entire database served from static files.

**Disk images.** Virtual machine images, ISO files, anything that is a contiguous byte sequence.

## The economics

GitHub Pages gives you a CDN-backed static file host with HTTPS, custom domains, and global distribution. The repository limit is generous (a few GB for most accounts). By keeping each file under 50MB, you avoid LFS and its associated costs.

The total cost of hosting and serving a 179MB audiobook to unlimited listeners: $0.00/month. The bandwidth comes from GitHub's CDN. The storage comes from the git repository. The compute comes from the listener's browser.

## The pattern

When a platform imposes a size limit on individual files but not on the total number of files, sharding turns one file into many. The manifest preserves the logical unity of the original file while the physical representation respects the platform's constraints.

This is not a hack. This is how every distributed storage system works internally -- HDFS, S3 multipart uploads, BitTorrent piece files. The difference is that we are doing it at the application layer with a 332-line Python script instead of at the infrastructure layer with a distributed storage service.
