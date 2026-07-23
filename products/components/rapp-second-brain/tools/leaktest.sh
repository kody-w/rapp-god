#!/bin/bash
# leaktest.sh — exact private-name leak test for the public hemisphere. Run
# locally (needs gh auth to read the private-name denylist). Zero exit = clean.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
gh repo list kody-w --limit 500 --json name,visibility \
  --jq '.[]|select(.visibility=="PRIVATE")|.name' > /tmp/.rapp-priv-names
python3 - <<'PY'
import re,glob,os
priv={l.strip() for l in open('/tmp/.rapp-priv-names') if l.strip()}
tok=set()
for f in glob.glob('brain/**/*',recursive=True):
    if os.path.isfile(f):
        tok|=set(re.findall(r'kody-w/([A-Za-z0-9._-]+)',open(f,errors='ignore').read()))
leaks=sorted(tok&priv)
print('LEAK' if leaks else 'CLEAN', leaks if leaks else f'({len(priv)} private names, none in public brain)')
import sys; sys.exit(1 if leaks else 0)
PY
