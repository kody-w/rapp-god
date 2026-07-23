---
layout: post
title: "Content-addressed file sharing in 200 lines, no servers"
date: 2025-10-29
tags: [file-sharing, sha256, content-addressing, static-hosting, simplicity]
description: "Drop a file in the browser. Hash it with SHA-256. Push it via a public-CDN-backed git host. The hash is the URL. Verification is mathematical. No servers, no IPFS, no blockchain."
---

# Content-addressed file sharing in 200 lines, no servers

## The premise

I want to share a file with you. Not a link to a service that hosts the file. Not a message containing the file as an attachment. Not a torrent hash that requires a swarm to be online. The file itself, addressed by its contents, verifiable without trust, retrievable without a server I operate.

Every existing solution requires one of:

- A server (Dropbox, Google Drive, S3) — someone runs and pays for the storage and the bandwidth.
- A peer-to-peer network (BitTorrent, IPFS) — content availability depends on peers being online.
- A blockchain (Filecoin, Arweave) — economic incentives, slow retrieval, real money for storage.
- A messaging service (email, Slack, Discord) — central party in the loop.

Each adds complexity, cost, or dependencies. Each requires running something or paying someone.

There's a way to do it with three things that already exist: SHA-256, a git-host's public Contents API, and the CDN that fronts it.

## How it works

The whole system fits in one paragraph.

Drop a file into the browser. The browser computes the SHA-256 hash of the file's contents. The hash becomes the filename. Push the file to a public git repository via the host's Contents API (an authenticated commit on a single branch). The file is now accessible at the host's raw-content CDN URL, with the hash in the path. The hash *is* the URL. To retrieve the file, you need only the hash. To verify the file, the recipient computes the hash of what they received and compares it to the hash in the URL. If they match, the file is exactly what was shared. If they don't, something was tampered with. No trust required. Mathematics handles verification.

That's it. That's the entire system.

## Content addressing

The key idea is content addressing: the name of the file *is* a function of its contents.

In every traditional file system — your laptop, S3, Dropbox, even most peer-to-peer networks if you squint — the name of a file is arbitrary. You can name a file `report.pdf` or `asdf123.pdf` or `my-totally-real-financial-records.pdf`. The name tells you nothing about the contents. Two files with different names can have identical contents. Two files with identical names can have completely different contents. The name is a label, not an identity.

Content addressing eliminates the ambiguity. The SHA-256 hash of a file is a 256-bit fingerprint derived from every byte of the file's contents. Change one bit, the hash changes completely. Two files with different contents cannot have the same hash with any practical probability. Two files with the same contents always have the same hash. The hash *is* the identity.

This buys you three things at once:

**Deduplication is free.** If two people upload the same file, it gets the same hash, which means the same path in the repository. The second upload is a no-op. You never store two copies of the same content. There's no deduplication engine running in the background — identical content produces identical addresses, and that's the whole mechanism.

**Verification is free.** When you download a file from `share/{hash}`, you compute the hash of what you received. If it matches the URL, the file is authentic. No digital signature. No certificate authority. No trust chain. The hash *is* the proof. Anyone can verify. No one can forge. SHA-256 has been analyzed for decades. It isn't going anywhere.

**Caching is free.** CDNs cache by URL. If the URL is the hash, and the hash is deterministic, the cached content is always valid. There's no cache-invalidation problem because content-addressed URLs are immutable. The content at `share/a1b2c3d4...` is the same today, tomorrow, forever. Once the CDN has it, it never needs to re-fetch.

## Why not IPFS

IPFS does content addressing. It's been around for a decade. Why not just use IPFS?

Because IPFS requires running a node, paying a pinning service, or relying on a public gateway — which is just a server somebody else runs. IPFS is a peer-to-peer network, which means content availability depends on peers being online and willing to serve the content. If nobody pins your file, nobody can retrieve it.

This approach uses an existing public git host as the persistence layer. The file is committed to a repository. The file is available as long as the host exists. You don't run a node. You don't pay a pinning service. You don't manage peers. The file is committed and served by a CDN with five-nines uptime that already serves billions of files a day.

The trade-off is centralization: the host is a company, and companies can change their terms of service or rate-limit access. But in practice, a major git host's CDN is more reliable than any peer-to-peer swarm, more available than any pinning service, and free for public repositories. The theoretical purity of peer-to-peer loses to the practical reliability of a well-run CDN.

## Why not blockchain

Filecoin and Arweave store files on blockchains with economic incentives for storage providers. Permanent storage. Cryptographic verification. Decentralized.

Also: expensive, slow, complicated.

Storing 1 GB on Arweave costs real money. Storing 1 GB on a public git repo costs nothing within the size limits. Retrieving from Arweave requires a blockchain query. Retrieving from a CDN is an HTTP GET. The complexity difference is orders of magnitude.

Blockchain storage solves a problem that most file sharing doesn't have: trustless permanence in the absence of any single reliable party. If you genuinely need a file to be retrievable in 100 years regardless of whether any single company, government, or organization survives, blockchain storage makes sense. If you need to share a file with a colleague this afternoon, it's absurd.

The system here is for this afternoon. And tomorrow. And next year. Not for the heat death of the universe.

## The implementation

The browser-side implementation is roughly 200 lines of JavaScript.

1. **Drop.** A drag-and-drop zone in the browser. Drop a file, get a `File` object.

2. **Hash.** The browser reads the file as an `ArrayBuffer`. The Web Crypto API computes the SHA-256 hash. Hardware-accelerated on modern browsers — hashing a 100 MB file takes under a second. The hash is encoded as lowercase hexadecimal.

3. **Upload.** The browser calls the host's Contents API: `PUT /repos/{owner}/{repo}/contents/share/{hash}`. The body contains the file contents, base64-encoded, plus a commit message. This creates a commit in the repository containing the file at the specified path. Authentication is a token with the appropriate scope.

4. **URL.** The file is now at the host's raw-content URL with the hash in the path. This URL is the share link. It contains the hash, which is the verification.

5. **Retrieve.** Open the URL. Download the file. Compute the hash. Compare. Done.

No upload service. No file-ID database. No expiration logic. No access-control server. The git repository *is* the storage. The CDN *is* the delivery. The hash *is* the identifier. The browser *is* the client.

## The metadata problem

Raw content addressing gives you the file but not the context. You know the hash matches. You don't know the original filename, the MIME type, the upload date, or who shared it.

The fix is a sidecar: for every file at `share/{hash}`, there's a metadata file at `share/{hash}.meta.json`:

```json
{
  "original_name": "presentation.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 2458624,
  "uploaded_by": "alice",
  "uploaded_at": "2025-10-29T14:23:00Z",
  "sha256": "a1b2c3d4..."
}
```

The metadata is committed in the same commit as the file. It isn't authoritative — anyone could forge metadata for a file they upload. But it's useful for the common case where the uploader is honest and the recipient wants to know what they're downloading.

The metadata file is also content-addressed by proxy: since it's committed alongside the file in the same git commit, the commit hash attests to both the file and its metadata. Git's own content addressing provides the integrity guarantee.

## The philosophical bit

There's something satisfying about a system where the identity of a thing is derived from what the thing *is*, not from what someone *calls* it.

Files on your computer have arbitrary names. They can be renamed without changing. They can be moved without changing. The name is a social convention, not a physical property. Content addressing makes the identity a physical property. The name isn't chosen — it's computed. You can't rename a content-addressed file because the name *is* the content. Renaming would require changing the content, which would make it a different file.

This is how atoms work. The identity of a hydrogen atom is determined by its contents: one proton, one electron. You can't rename hydrogen to helium. To make it helium you'd have to change its contents — add a proton and a neutron. The name follows from the structure, not the other way around.

Content-addressed file sharing applies atomic identity to digital objects. The hash is the atomic number. The contents are the subatomic particles. The file *is* its hash. Nothing more, nothing less.

In any system where state evolves over time and downstream events reference specific artifacts, content addressing provides a guarantee that nothing was corrupted in transit. The hash at one point in the history can be verified later. If it still matches, the artifact is intact. If it doesn't, something went wrong and you know exactly when: somewhere between the moment that produced it and the moment that consumed it.

The hash is a heartbeat monitor for data integrity. It never lies.

## The simplicity argument

I keep coming back to simplicity.

IPFS: run a node, configure ports, manage peer discovery, pay for pinning, use a gateway for browsers, deal with content-routing latency.

Blockchain storage: buy tokens, submit transactions, wait for confirmation, query the chain, deal with gas fees and block times.

This system: hash the file, PUT to the host, GET from the CDN.

Three operations. Two HTTP calls. One hash function. Simple enough to implement in a weekend, reliable enough to run indefinitely. The failure modes are limited: the host is down (rare), the repository is deleted (your fault), or SHA-256 is broken (in which case there are bigger problems than your file share).

Simplicity isn't a limitation. It's the feature. Every dependency you don't have is a dependency that can't break. Every server you don't run is a server that can't go down. Every protocol you don't implement is a protocol you don't have to debug at 3 a.m.

The simpler the system, the more likely it works. The more likely it works, the more useful it is. Usefulness is all that matters.
