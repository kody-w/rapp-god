#!/usr/bin/env bash
# rapp-god re-sync — pull every canonical source into snapshot/ and refresh the manifest
# (bytes + sha256) so Lens A goes green again. Run this after a canonical source intentionally
# changes. Does NOT touch Lens B (cross-repo drift is reconciled at the source, not here).
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import json, hashlib, os, urllib.request
m = json.load(open('manifest.json'))
def fetch(u):
    with urllib.request.urlopen(u, timeout=30) as r: return r.read()
changed = 0
for c in m['tracked']:
    for f in c['files']:
        data = fetch(f['canonical'])
        os.makedirs(os.path.dirname(f['snapshot']), exist_ok=True)
        old = open(f['snapshot'], 'rb').read() if os.path.exists(f['snapshot']) else None
        if old != data:
            open(f['snapshot'], 'wb').write(data); changed += 1
            print(f"  updated  {f['snapshot']}")
        f['bytes'] = len(data); f['sha256'] = hashlib.sha256(data).hexdigest()
json.dump(m, open('manifest.json', 'w'), indent=2, ensure_ascii=False)
open('manifest.json', 'a').write("\n")
print(f"re-synced {sum(len(c['files']) for c in m['tracked'])} files · {changed} changed · manifest refreshed")
PY
