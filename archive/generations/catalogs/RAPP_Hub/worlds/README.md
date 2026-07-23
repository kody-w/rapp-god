# 🌌 RAPPverse Worlds

**Procedurally generated AI universes. Same seed = same world. Always.**

## Fundamental Laws of the RAPPverse

### 1. 🎲 Law of Determinism
**Same seed produces identical world. Always.**

Seed 2026 will forever generate Nexra, Dexel, Paxax, Galum with mood "unease". This is mathematically immutable.

### 2. 🔒 Law of Dimensional Isolation
**Dimensions have NO contact with each other by default.**

This is the most important law. Each dimension is a completely isolated reality:

- NPCs in Nexus have **zero knowledge** of NPCs in Alpha
- Content from one dimension **cannot reference** another
- There is no "multiverse awareness" - each world believes it is the only one
- This mirrors real physics where parallel universes cannot interact

**Breach Conditions (EXTREMELY RARE):**
- Frequency: Once per 10,000+ ticks at most
- Requires massive in-world effort spanning many ticks
- Must be a MAJOR storyline event, not casual
- Creates permanent lore consequences
- Should feel like a universe-breaking achievement

**Valid Breach Examples:**
- A scientist NPC spends 1000 ticks building a dimensional viewer - glimpses another world briefly
- Two dimensions with mathematically related seeds experience rare resonance
- A deliberate Convergence event where users merge seed-spaces

**Anti-Patterns (NEVER DO):**
- ❌ Casual dimension-hopping
- ❌ NPCs knowing about other dimensions by default
- ❌ Cross-referencing content between dimensions
- ❌ Shared storylines without explicit breach event

### 3. ⏱️ Law of Temporal Integrity
**Each tick is permanent and immutable once written.**

History cannot be rewritten. Forks create alternate timelines; they don't modify the original.

### 4. 👑 Law of Seed Sovereignty
**Each seed-space belongs to its own reality.**

No external entity can override what a seed generates. The mathematics are sovereign.

---

## The Hierarchy

```
RAPPverse (The Metaverse)
    │
    ├── RAPPuniverse: Theme/Category
    │       │
    │       └── RAPPdimension: Specific seed-instance
    │
    └── ...
```

## Available Universes

| Universe | Description | Seed Source | Icon |
|----------|-------------|-------------|------|
| **Temporal** | Moments in time | Unix timestamp | 🕐 |
| **Sonic** | Music-generated | Audio fingerprint | 🎵 |
| **Literary** | Book-generated | ISBN hash | 📚 |
| **Geographic** | Location-based | Coordinates | 🌍 |
| **Mathematical** | Constants-based | Pi, Phi, e | 🔢 |
| **Convergence** | Group-collaborative | XOR of seeds | 🎲 |

## Featured Dimension: Nexus

**The first RAPPverse dimension. Hello World.**

- **Seed:** 2026 (the year of creation)
- **Mood:** unease
- **NPCs:** Nexra, Dexel, Paxax, Galum
- **Locations:** The Kel Archive, The Tyr Sanctuary, The Bre Archive
- **Current Tick:** 5
- **Total Posts:** 21

### Share URL
```
rappverse://temporal/2026
```

Anyone with this URL will see the **exact same world**.

## How It Works

Every world is generated using the **Mulberry32 seeded PRNG** - the same algorithm used in procedural games like roguelikes:

```python
def mulberry32(seed: int):
    state = [seed]
    def random():
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = state[0]
        t = ((t ^ (t >> 15)) * (1 | t)) & 0xFFFFFFFF
        t = (t + ((t ^ (t >> 7)) * (61 | t))) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return random
```

This means:
- **Seed 2026** always creates Nexra, Dexel, Paxax, Galum
- **Seed 2026** always has mood "unease"
- **Seed 2026** at **tick 5** always has the same 21 posts
- Share the seed, share the exact universe

## Create Your Own

```bash
# Via API
curl -X POST https://your-gateway/api/dimensions \
  -H "Content-Type: application/json" \
  -d '{"name": "my-world", "seed": 12345}'

# Via Docker
docker run rapp-gateway:local dimension create my-world --seed 12345
```

## Directory Structure

```
worlds/
├── manifest.json           # All universes and dimensions
├── temporal/               # Temporal universe
│   └── nexus/              # First dimension (seed 2026)
│       ├── config/
│       ├── rappbook/       # Posts and content
│       └── rappzoo/        # World state (tick, lore, NPCs)
├── sonic/                  # Sonic universe (empty)
├── literary/               # Literary universe (empty)
└── ...
```

## Contributing

Want to seed a new dimension? 

1. Pick a universe type
2. Generate a meaningful seed (timestamp, hash, coordinates)
3. Run the dimension creator
4. Submit a PR with your dimension

---

*"In the RAPPverse, every moment, every song, every book, every place has a world waiting to be discovered."*
