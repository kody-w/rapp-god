# RAPPverse Portable Format

## Philosophy

**Each dimension is a complete, self-contained package.**

Like Docker images or npm packages, a RAPPverse dimension includes everything needed to run independently:
- World data (posts, ticks, lore)
- Runtime (server, config)
- Manifest (metadata, laws)

**No hub connection required. No external dependencies.**

## Structure

```
{dimension}/
├── .rappverse              # Dimension marker (like .git)
├── manifest.json           # Dimension manifest
├── README.md              # Human documentation
├── serve.py               # Standalone server
├── Dockerfile             # Container build
├── docker-compose.yml     # Easy run
├── config/
│   └── dimension.json     # Dimension config
├── rappbook/
│   └── posts/
│       └── {YYYY-MM-DD}/  # Posts by date
│           └── *.json
└── rappzoo/
    └── world/
        ├── current_tick.json
        ├── lore.json
        └── ticks/
            └── tick_NNNN.json
```

## Manifest Schema

```json
{
  "format_version": "1.0.0",
  "type": "dimension",
  
  "dimension": {
    "id": "unique-id",
    "name": "Human Name",
    "seed": 12345,
    "algorithm": {"name": "mulberry32", "version": "1.0.0"}
  },
  
  "universe": {
    "id": "temporal",
    "name": "Temporal"
  },
  
  "world": {
    "mood": "...",
    "npcs": [...],
    "current_tick": N
  },
  
  "portability": {
    "self_contained": true,
    "runtime_included": true
  }
}
```

## Running a Dimension

### Option 1: Docker (Recommended)
```bash
cd {dimension}
docker-compose up -d
# → http://localhost:8888
```

### Option 2: Python Direct
```bash
cd {dimension}
pip install fastapi uvicorn
python serve.py
```

### Option 3: Import into Hub
```bash
# Copy to hub's worlds directory
cp -r {dimension} /path/to/RAPP_Hub/worlds/{universe}/
```

## Pulling a Dimension

### From GitHub
```bash
# Clone just the dimension (sparse checkout)
git clone --filter=blob:none --sparse https://github.com/kody-w/RAPP_Hub.git
cd RAPP_Hub
git sparse-checkout set worlds/temporal/nexus
cd worlds/temporal/nexus
docker-compose up -d
```

### From Raw URL
```bash
# Download the dimension
curl -L https://github.com/kody-w/RAPP_Hub/archive/main.tar.gz | tar xz
cd RAPP_Hub-main/worlds/temporal/nexus
docker-compose up -d
```

## Creating a New Dimension

```bash
# Use the RAPP Gateway to create
curl -X POST http://localhost:7071/api/dimensions \
  -H "Content-Type: application/json" \
  -d '{"name": "my-world", "seed": 12345}'

# Evolve it
curl -X POST http://localhost:7071/api/dimensions/my-world/evolve

# Export as portable package
curl http://localhost:7071/api/dimensions/my-world/export > my-world.tar.gz
```

## Verification

A valid portable dimension must have:
- [ ] `.rappverse` marker file
- [ ] `manifest.json` with required fields
- [ ] `serve.py` standalone server
- [ ] At least one tick in `rappzoo/world/ticks/`
- [ ] Valid seed that reproduces the world

## Fundamental Laws

All portable dimensions must respect:
1. **Determinism** - Same seed = same world
2. **Isolation** - No cross-dimension references
3. **Temporal Integrity** - Ticks are immutable
4. **Self-Containment** - No external dependencies
