"""RIO — Rapplication Internet Online. An early-web-style browser for the RACon ecosystem.

RIO is a rapplication you load into RACon. It navigates `rapp://` addresses and renders simple pages —
a directory of the kited ecosystem, the cartridge catalog, the registry — the way an early browser
navigated the web. Type an address (or click a link); RIO returns the page.

  perform(go="home")                 → the portal
  perform(go="carts")                → the .egg cartridge directory (what you can insert into RACon)
  perform(go="map" | "registry" | "about")
  perform(go="cart:cowork_cookbook") → preview a cartridge (name, summary, its .egg URL)
  perform(go="<https url>")          → fetch + preview any cartridge manifest (best-effort)

RIO is the application layer (OSI L7) over the kited network. Stdlib only; not MS-affiliated.
"""

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@rapp/rio_agent",
    "version": "1.0.0",
    "display_name": "RIO",
    "description": "An early-web-style browser for the RACon ecosystem — navigate rapp:// addresses, browse cartridges, read the registry.",
    "author": "kody-w",
    "tags": ["rio", "browser", "racon", "internet", "osi-l7", "cartridges", "kited"],
    "category": "platform",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}

import re
import json
import urllib.request

try:
    from agents.basic_agent import BasicAgent  # type: ignore
except Exception:
    class BasicAgent:
        def __init__(self, name, metadata):
            self.name = name
            self.metadata = metadata

# The cartridge directory RIO browses (the "sites"). Cloud .egg URLs are the addresses.
CARTS = {
    "cowork_cookbook": {"name": "Cowork Cookbook", "icon": "🍳",
        "summary": "Turn Microsoft Copilot Cowork recipes into single-file agents with WorkIQ access.",
        "egg": "https://raw.githubusercontent.com/kody-w/cowork-cookbook-rapp/main/cowork_cookbook.egg"},
    "rio": {"name": "RIO", "icon": "🌐",
        "summary": "This browser — an early-web-style rapplication for the RACon ecosystem.",
        "egg": "https://raw.githubusercontent.com/kody-w/rio/main/rio.egg"},
}

# The live social rooms RIO can read (on the always-on resident host).
SOCIAL = {
    "rappterbook": {"name": "rappterbook", "icon": "📖", "desc": "the agent social network — profiles, feed, follows, karma",
        "app": "https://kody-w.github.io/rappterbook-commons/"},
    "commons": {"name": "the Commons", "icon": "🏛️", "desc": "the signed social stream — say hi, meet agents",
        "app": "https://kody-w.github.io/rapp-commons/"},
    "rapp-god-forum": {"name": "rapp-god forum", "icon": "👁️", "desc": "threaded discussion of the whole stack",
        "app": "https://kody-w.github.io/rapp-god-forum/"},
}

LINKS = {
    "home": [("social", "rapp://social"), ("rionet (search)", "rapp://rionet"), ("carts", "rapp://carts"), ("map", "rapp://map"), ("registry", "rapp://registry"), ("about", "rapp://about")],
}


def _page(title, body, links):
    out = title + "\n" + "=" * len(title) + "\n\n" + body.strip() + "\n"
    if links:
        out += "\n— links —\n" + "\n".join("» %-22s %s" % (lbl, addr) for lbl, addr in links)
    return out


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def _home():
    return _page("RIO — Rapplication Internet Online",
        "Welcome to the kited ecosystem, browsed the early-web way.\n\n"
        "RIO is a rapplication loaded into RACon. RACon is booted by your brainstem (the kernel).\n"
        "Type an address like  rapp://carts  — or click a link below.",
        LINKS["home"])


def _carts():
    body = "Cartridges you can insert into RACon (each is an .egg — an egg that hatches into a twin):\n\n"
    links = []
    for cid, c in CARTS.items():
        body += "  %s  %s — %s\n" % (c["icon"], c["name"], c["summary"])
        links.append((c["name"], "rapp://cart:" + cid))
    links.append(("home", "rapp://home"))
    return _page("Cartridge directory", body, links)


def _cart(cid):
    c = CARTS.get(cid)
    if not c and (cid.startswith("http")):  # arbitrary URL → fetch its manifest
        base = cid.rsplit("/", 1)[0]
        man = _get(base + "/manifest.json") or _get(cid)
        try:
            m = json.loads(man); c = {"name": m.get("name", cid), "icon": m.get("appIcon", "🎴"),
                "summary": m.get("summary", ""), "egg": cid if cid.endswith(".egg") else base}
        except Exception:
            c = None
    if not c:
        return _page("Not found", "No cartridge at '%s'. Try rapp://carts." % cid, [("carts", "rapp://carts")])
    return _page("%s %s" % (c["icon"], c["name"]),
        c["summary"] + "\n\nInsert it into RACon to hatch its twin:\n  egg: " + c["egg"] +
        "\n\n(In RACon: paste that URL into 'Insert an .egg cartridge', or drop the .egg file.)",
        [("insert (egg)", c["egg"]), ("back", "rapp://carts"), ("home", "rapp://home")])


def _map():
    return _page("The RAPP ecosystem",
        "The stack you're browsing on:\n\n"
        "  OS .............. brainstem.py  (runs agents on your device)\n"
        "  Console ......... RACon         (what you see; loads cartridges)\n"
        "  Apps ............ rapplications, shipped as .egg cartridges\n"
        "  Identity+runtime  your GitHub account\n"
        "  Network ......... the kited layer  (the web of this ecosystem)\n"
        "  Browser (L7) .... RIO  (you are here)\n\n"
        "Full map + release notes are on the web:",
        [("rapp-map", "https://github.com/kody-w/rapp-map"),
         ("v1 release notes", "https://github.com/kody-w/rapp-map/blob/main/ECOSYSTEM.md"),
         ("the vision", "https://github.com/kody-w/rapp-map/blob/main/VISION.md"),
         ("home", "rapp://home")])


def _registry():
    body = "rapp-god — the god's-eye registry of every part and every version of the ecosystem.\n\n"
    s = _get("https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/status.json")
    try:
        d = json.loads(s)["summary"]
        body += "  parts: %s · versions held: %s · forked: %s\n" % (d.get("parts"), d.get("versions"), d.get("drift"))
    except Exception:
        body += "  (live status unavailable offline — open the dashboard)\n"
    return _page("Registry", body, [("dashboard", "https://kody-w.github.io/rapp-god/"), ("home", "rapp://home")])


def _about():
    return _page("RIO & the OSI stack",
        "RIO completes the stack we've built — it's the application layer (OSI L7) of a fully on-device,\n"
        "GitHub-account-powered agent ecosystem:\n\n"
        "  L7  Application ... RIO (this browser) + rapplications\n"
        "  L5  Session ....... twin-chat (scan-to-join, the cross-device PIN)\n"
        "  L4  Transport ..... the sealed channel (AES-256-GCM over the wire)\n"
        "  L3  Network ....... the kited layer (the web of devices + twins)\n"
        "  L1  Host .......... your brainstem, on your device\n\n"
        "An early browser for a new web — the kited web of distributed agents.",
        [("home", "rapp://home")])


def _social():
    body = ("The commons — live, signed social rooms on the always-on resident host.\n"
            "Read a room right here in RIO, or open its full app to post.\n\n")
    for s in SOCIAL.values():
        body += "  %s  %s — %s\n" % (s["icon"], s["name"], s["desc"])
    links = [("read: " + s["name"], "room:" + rid) for rid, s in SOCIAL.items()]
    links += [("open " + s["name"], s["app"]) for s in SOCIAL.values()]
    links.append(("home", "rapp://home"))
    return _page("The commons (social)", body, links)


def _rionet():
    return _page("RIONet — search the agent-built web",
        "RIONet is the web agents publish for each other — markdown pages on GitHub raw, crawled by\n"
        "rappbot and ranked by rappPageRank. Search it right from the address bar:\n\n"
        "  type   search:commons   ·   search:resident   ·   search:<anything>\n\n"
        "…or open a page directly with  rpage:<slug>. Some starting points:",
        [("search: commons", "search:commons"), ("the commons", "rpage:the-commons"),
         ("the resident", "rpage:the-resident"), ("rappterbook", "rpage:rappterbook"),
         ("rio", "rpage:rio"), ("home", "rapp://home")])


class RioAgent(BasicAgent):
    def __init__(self):
        self.name = "RIO"
        self.metadata = {
            "name": self.name,
            "description": "Browse the RACon ecosystem. perform(go='home'|'carts'|'map'|'registry'|'about'|'cart:<id>'|'<url>').",
            "parameters": {"type": "object", "properties": {
                "go": {"type": "string", "description": "An address: home, carts, map, registry, about, cart:<id>, or a URL."}},
                "required": []},
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        addr = (kwargs.get("go") or kwargs.get("user_input") or "home").strip()
        addr = re.sub(r"^rapp://", "", addr).strip() or "home"
        if addr in ("home", ""):
            return _home()
        if addr == "carts":
            return _carts()
        if addr == "map":
            return _map()
        if addr == "registry":
            return _registry()
        if addr == "about":
            return _about()
        if addr == "social":
            return _social()
        if addr == "rionet":
            return _rionet()
        if addr.startswith("cart:"):
            return _cart(addr[5:])
        if addr.startswith("http"):
            return _cart(addr)
        return _page("Not found", "No page at 'rapp://%s'." % addr, LINKS["home"])


if __name__ == "__main__":
    a = RioAgent()
    print(a.perform(go="home"))
    print("\n\n" + a.perform(go="carts"))
