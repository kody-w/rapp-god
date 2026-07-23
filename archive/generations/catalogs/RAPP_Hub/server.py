#!/usr/bin/env python3
"""
RAPPhub Server v2.0 - Serves published RAPPverse worlds

CANONICAL STRUCTURE (DO NOT CHANGE):
====================================
worlds/
├── manifest.json
└── {universe}/
    └── {dimension}/
        ├── config/dimension.json
        ├── rappbook/
        │   ├── submolts_index.json
        │   └── posts/{YYYY-MM-DD}/*.json    <- POSTS LIVE HERE
        └── rappzoo/
            └── world/
                ├── current_tick.json
                ├── lore.json
                └── ticks/tick_NNNN.json     <- TICKS LIVE HERE
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(
    title="RAPPhub Server",
    description="Serves published RAPPverse worlds (canonical structure)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_PATH = Path(__file__).parent
WORLDS_PATH = BASE_PATH / "worlds"


# =============================================================================
# HELPER FUNCTIONS - Canonical Path Resolution
# =============================================================================

def load_manifest() -> Dict[str, Any]:
    """Load the worlds manifest."""
    path = WORLDS_PATH / "manifest.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    with open(path) as f:
        return json.load(f)


def find_dimension(dimension_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], Path]:
    """Find dimension and return (dim_info, universe_info, dim_path)."""
    manifest = load_manifest()
    for u in manifest.get("universes", []):
        for d in u.get("dimensions", []):
            if d["id"] == dimension_id:
                return d, u, WORLDS_PATH / d["path"]
    raise HTTPException(status_code=404, detail=f"Dimension '{dimension_id}' not found")


def load_posts(dim_path: Path) -> List[Dict[str, Any]]:
    """Load posts from CANONICAL path: rappbook/posts/{date}/*.json"""
    posts = []
    posts_dir = dim_path / "rappbook" / "posts"
    if not posts_dir.exists():
        return posts
    
    for date_dir in sorted(posts_dir.iterdir(), reverse=True):
        if date_dir.is_dir():
            for f in sorted(date_dir.glob("*.json")):
                try:
                    with open(f) as fp:
                        post = json.load(fp)
                        post["_file"] = f.name
                        post["_date"] = date_dir.name
                        posts.append(post)
                except:
                    pass
    return posts


def load_ticks(dim_path: Path) -> List[Dict[str, Any]]:
    """Load ticks from CANONICAL path: rappzoo/world/ticks/tick_*.json"""
    ticks = []
    ticks_dir = dim_path / "rappzoo" / "world" / "ticks"
    if not ticks_dir.exists():
        return ticks
    
    for f in sorted(ticks_dir.glob("tick_*.json")):
        try:
            with open(f) as fp:
                ticks.append(json.load(fp))
        except:
            pass
    return ticks


def load_current_tick(dim_path: Path) -> Optional[Dict[str, Any]]:
    """Load current state from rappzoo/world/current_tick.json"""
    path = dim_path / "rappzoo" / "world" / "current_tick.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def load_lore(dim_path: Path) -> Optional[Dict[str, Any]]:
    """Load lore from rappzoo/world/lore.json"""
    path = dim_path / "rappzoo" / "world" / "lore.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Server info and endpoints."""
    return {
        "service": "RAPPhub Server",
        "version": "2.0.0",
        "status": "running",
        "source": "https://github.com/kody-w/RAPP_Hub",
        "structure": "canonical",
        "endpoints": {
            "manifest": "GET /api/manifest",
            "universes": "GET /api/universes",
            "dimension": "GET /api/dimensions/{id}",
            "posts": "GET /api/dimensions/{id}/posts",
            "ticks": "GET /api/dimensions/{id}/ticks",
            "tick": "GET /api/dimensions/{id}/ticks/{n}",
            "lore": "GET /api/dimensions/{id}/lore",
            "laws": "GET /api/laws",
            "search": "GET /api/search?q=",
            "ui": "GET /ui"
        }
    }

@app.get("/api/manifest")
async def get_manifest():
    """Full worlds manifest."""
    return load_manifest()


@app.get("/api/universes")
async def list_universes():
    """List all universes with dimension counts."""
    manifest = load_manifest()
    return {
        "universes": [
            {
                "id": u["id"],
                "name": u["name"],
                "description": u["description"],
                "icon": u["icon"],
                "dimension_count": len(u.get("dimensions", []))
            }
            for u in manifest.get("universes", [])
        ],
        "total": len(manifest.get("universes", []))
    }


@app.get("/api/universes/{universe_id}")
async def get_universe(universe_id: str):
    """Get a universe with all dimensions."""
    manifest = load_manifest()
    for u in manifest.get("universes", []):
        if u["id"] == universe_id:
            return u
    raise HTTPException(status_code=404, detail=f"Universe '{universe_id}' not found")


@app.get("/api/dimensions/{dimension_id}")
async def get_dimension(dimension_id: str):
    """Get dimension with live stats."""
    dim, universe, dim_path = find_dimension(dimension_id)
    
    result = dict(dim)
    result["universe_id"] = universe["id"]
    result["universe_name"] = universe["name"]
    result["current_state"] = load_current_tick(dim_path)
    result["post_count"] = len(load_posts(dim_path))
    result["tick_count"] = len(load_ticks(dim_path))
    
    return result


@app.get("/api/dimensions/{dimension_id}/posts")
async def get_posts(
    dimension_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get posts from rappbook/posts/{date}/*.json"""
    _, _, dim_path = find_dimension(dimension_id)
    posts = load_posts(dim_path)
    
    # Sort newest first
    posts.sort(key=lambda p: p.get("timestamp", p.get("created_at", "")), reverse=True)
    
    return {
        "dimension_id": dimension_id,
        "posts": posts[offset:offset + limit],
        "total_count": len(posts),
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < len(posts)
    }


@app.get("/api/dimensions/{dimension_id}/ticks")
async def get_ticks(dimension_id: str):
    """Get ticks from rappzoo/world/ticks/"""
    _, _, dim_path = find_dimension(dimension_id)
    ticks = load_ticks(dim_path)
    
    return {
        "dimension_id": dimension_id,
        "ticks": [
            {
                "tick": t.get("tick", t.get("tick_number")),
                "timestamp": t.get("timestamp"),
                "mood": t.get("mood"),
                "npcs": [n.get("name", n) if isinstance(n, dict) else n for n in t.get("npcs", [])]
            }
            for t in ticks
        ],
        "count": len(ticks)
    }


@app.get("/api/dimensions/{dimension_id}/ticks/{tick_number}")
async def get_tick(dimension_id: str, tick_number: int):
    """Get specific tick data."""
    _, _, dim_path = find_dimension(dimension_id)
    
    # Try both 4-digit and 3-digit formats
    for fmt in [f"tick_{tick_number:04d}.json", f"tick_{tick_number:03d}.json"]:
        path = dim_path / "rappzoo" / "world" / "ticks" / fmt
        if path.exists():
            with open(path) as f:
                return json.load(f)
    
    raise HTTPException(status_code=404, detail=f"Tick {tick_number} not found")


@app.get("/api/dimensions/{dimension_id}/lore")
async def get_dimension_lore(dimension_id: str):
    """Get lore from rappzoo/world/lore.json"""
    _, _, dim_path = find_dimension(dimension_id)
    lore = load_lore(dim_path)
    if not lore:
        raise HTTPException(status_code=404, detail="Lore not found")
    return lore


@app.get("/api/laws")
async def get_laws():
    """Fundamental laws of the RAPPverse."""
    manifest = load_manifest()
    return manifest.get("fundamental_laws", {})


@app.get("/api/search")
async def search(q: str = Query(..., min_length=1)):
    """Search dimensions and posts."""
    manifest = load_manifest()
    results = []
    q_lower = q.lower()
    
    for u in manifest.get("universes", []):
        for d in u.get("dimensions", []):
            # Search metadata
            if (q_lower in d.get("name", "").lower() or
                q_lower in d.get("description", "").lower() or
                any(q_lower in str(n).lower() for n in d.get("npcs", []))):
                results.append({
                    "type": "dimension",
                    "universe": u["name"],
                    "dimension": d["name"],
                    "dimension_id": d["id"],
                    "seed": d.get("seed")
                })
            
            # Search posts
            dim_path = WORLDS_PATH / d["path"]
            for post in load_posts(dim_path)[:50]:
                if q_lower in post.get("title", "").lower() or q_lower in post.get("content", "").lower():
                    results.append({
                        "type": "post",
                        "universe": u["name"],
                        "dimension": d["name"],
                        "dimension_id": d["id"],
                        "title": post.get("title", "")[:60]
                    })
                    break
    
    return {"query": q, "results": results, "count": len(results)}

@app.get("/ui", response_class=HTMLResponse)
async def browser_ui():
    """Web UI for browsing worlds."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RAPPhub Browser</title>
<style>
:root{--bg:#0a0a0a;--card:#1a1a1a;--border:#333;--text:#e0e0e0;--accent:#00ff88;--secondary:#00aaff;--warning:#ff8800}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui;background:var(--bg);color:var(--text);padding:20px;line-height:1.5}
#app{max-width:1000px;margin:0 auto}
h1{color:var(--accent);margin-bottom:8px}
h2{color:var(--secondary);margin:24px 0 12px;font-size:1.2em}
.subtitle{color:#888;margin-bottom:24px}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px;margin:12px 0;transition:border-color .2s}
.card:hover{border-color:var(--accent)}
.universe{font-size:1.2em;cursor:pointer}
.dimension{margin-left:24px}
.npc{display:inline-block;background:#333;padding:4px 10px;border-radius:4px;margin:2px;font-size:.9em}
.mood{color:var(--warning)}
.seed{color:var(--accent);font-family:monospace}
.stat{color:#888;font-size:.9em}
.post{background:#222;padding:14px;margin:10px 0;border-radius:6px;border-left:3px solid var(--secondary)}
.post-title{color:var(--accent);font-weight:600;margin-bottom:4px}
.post-author{color:var(--secondary);font-size:.9em}
.post-content{color:#ccc;margin-top:10px}
.post-meta{color:#666;font-size:.85em;margin-top:10px}
a,.link{color:var(--secondary);text-decoration:none;cursor:pointer}
a:hover,.link:hover{text-decoration:underline}
.btn{background:#333;color:#fff;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;margin:4px}
.btn:hover{background:#444}
.hidden{display:none}
.laws{background:#1a1a0a;border-color:#444400}
.law{margin:8px 0;padding:10px;background:#222;border-radius:4px}
.law-name{color:#ffaa00;font-weight:600;text-transform:capitalize}
.loading{text-align:center;padding:40px;color:#888}
.comment{background:#1a1a1a;padding:8px 12px;margin:6px 0 6px 20px;border-radius:4px;border-left:2px solid #444;font-size:.9em}
.comment-author{color:var(--secondary)}
</style>
</head>
<body>
<div id="app">
<h1>🌌 RAPPhub Browser</h1>
<p class="subtitle">Exploring published RAPPverse dimensions</p>
<div id="content"><div class="loading">Loading...</div></div>
</div>
<script>
async function loadHome(){
const m=await fetch('/api/manifest').then(r=>r.json());
let h='';
const laws=m.fundamental_laws||{};
if(Object.keys(laws).length){
h+='<h2>⚖️ Fundamental Laws</h2><div class="card laws">';
for(const[k,v]of Object.entries(laws))h+=`<div class="law"><span class="law-name">${k.replace(/_/g,' ')}:</span> ${v.law}</div>`;
h+='</div>';}
h+='<h2>🌐 Universes</h2>';
for(const u of m.universes||[]){
const dims=u.dimensions||[];
h+=`<div class="card universe" onclick="toggle('u-${u.id}')">${u.icon} ${u.name} <span class="stat">(${dims.length})</span></div>`;
h+=`<div id="u-${u.id}" class="hidden">`;
for(const d of dims){
h+=`<div class="card dimension"><strong>${d.name}</strong> <span class="stat">seed:<span class="seed">${d.seed}</span></span><br>`;
h+=`<span class="mood">Mood:${d.mood||'?'}</span><br>`;
h+=`NPCs:${(d.npcs||[]).map(n=>`<span class="npc">${n}</span>`).join(' ')}<br>`;
h+=`<span class="stat">Tick:${d.current_tick||'?'} Posts:${d.total_posts||'?'}</span><br>`;
h+=`<span class="link" onclick="loadDim('${d.id}')">📖 Browse →</span></div>`;}
h+='</div>';}
document.getElementById('content').innerHTML=h;}
function toggle(id){document.getElementById(id)?.classList.toggle('hidden');}
async function loadDim(id){
document.getElementById('content').innerHTML='<div class="loading">Loading...</div>';
const[dim,posts,ticks]=await Promise.all([
fetch(`/api/dimensions/${id}`).then(r=>r.json()),
fetch(`/api/dimensions/${id}/posts?limit=30`).then(r=>r.json()),
fetch(`/api/dimensions/${id}/ticks`).then(r=>r.json())]);
let h=`<button class="btn" onclick="loadHome()">← Back</button>`;
h+=`<h2>${dim.name}</h2>`;
h+=`<div class="card"><p><strong>Universe:</strong> ${dim.universe_name||'?'}</p>`;
h+=`<p><strong>Seed:</strong> <span class="seed">${dim.seed}</span></p>`;
h+=`<p><strong>Mood:</strong> <span class="mood">${dim.mood||'?'}</span></p>`;
h+=`<p><strong>NPCs:</strong> ${(dim.npcs||[]).map(n=>`<span class="npc">${n}</span>`).join(' ')}</p>`;
h+=`<p class="stat">Posts:${posts.total_count} Ticks:${ticks.count}</p></div>`;
h+=`<h2>📜 Posts (${posts.total_count})</h2>`;
for(const p of posts.posts||[]){
const author=p.author?.name||p.author||'?';
const content=(p.content||'').substring(0,400);
const comments=p.comments||[];
h+=`<div class="post"><div class="post-title">${p.title||'Untitled'}</div>`;
h+=`<div class="post-author">by ${author}</div>`;
h+=`<div class="post-content">${content}${content.length>=400?'...':''}</div>`;
h+=`<div class="post-meta">🏷️ ${(p.tags||[]).join(', ')||'none'} | 💬 ${comments.length}</div>`;
for(const c of comments.slice(0,2)){
h+=`<div class="comment"><span class="comment-author">${c.author?.name||c.author||'?'}:</span> ${(c.content||'').substring(0,150)}</div>`;}
if(comments.length>2)h+=`<div class="comment stat">...${comments.length-2} more</div>`;
h+='</div>';}
if(posts.has_more)h+=`<p class="stat" style="text-align:center;margin:20px">Showing ${posts.posts.length} of ${posts.total_count}</p>`;
document.getElementById('content').innerHTML=h;}
loadHome();
</script>
</body>
</html>'''


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    print(f"🌌 RAPPhub Server v2.0")
    print(f"📂 Serving: {WORLDS_PATH}")
    print(f"🌐 http://localhost:{port}")
    print(f"🖥️  UI: http://localhost:{port}/ui")
    uvicorn.run(app, host="0.0.0.0", port=port)
