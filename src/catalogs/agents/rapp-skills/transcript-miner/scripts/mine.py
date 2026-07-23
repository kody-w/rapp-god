#!/usr/bin/env python3
"""mine.py — extract usage signals from Claude Code session JSONL archives.

Usage:
  python3 mine.py [--window N] [--min-bytes N] [--project SUBSTR] [--json OUT]

Emits, per corpus: tool histogram, top Bash command heads, error signatures,
skills used, permission denials, my-message categories (correction/rejection/
redirection), Read:Edit ratio distribution, and per-session rows. No network.
"""
import argparse, json, glob, os, collections, re, sys

CORR = re.compile(r'^(no|nope|stop|wrong|not that|thats not|that\'s not|dont|don\'t|actually)\b', re.I)
REJECT = re.compile(r'\b(you (test|do|build) it|dont make me|do it yourself|you can do)\b', re.I)


def mine(window, min_bytes, project):
    files = sorted(glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl')), key=os.path.getmtime)
    files = [f for f in files if os.path.getsize(f) > min_bytes]
    if project:
        files = [f for f in files if project in f]
    files = files[-window:]
    agg = dict(tools=collections.Counter(), bash=collections.Counter(),
               errors=collections.Counter(), skills=collections.Counter(),
               denials=0, corrections=[], rejections=[], sessions=[])
    for f in files:
        reads = edits = n_err = n_user = 0
        for line in open(f, errors='replace'):
            if len(line) > 2_000_000:
                continue
            try:
                j = json.loads(line)
            except Exception:
                continue
            t = j.get('type')
            if t == 'assistant':
                for c in j.get('message', {}).get('content', []):
                    if c.get('type') == 'tool_use':
                        nm = c.get('name', '?')
                        agg['tools'][nm] += 1
                        if nm == 'Read':
                            reads += 1
                        elif nm in ('Edit', 'Write', 'NotebookEdit'):
                            edits += 1
                        if nm == 'Bash':
                            cmd = str(c.get('input', {}).get('command', '')).strip()
                            head = re.split(r'[\s;|&]', cmd)[0][:30] if cmd else '?'
                            agg['bash'][head] += 1
                        if nm == 'Skill':
                            agg['skills'][str(c.get('input', {}).get('skill', '?'))] += 1
            elif t == 'user':
                cont = j.get('message', {}).get('content')
                texts = [cont] if isinstance(cont, str) else \
                    [c.get('text', '') for c in cont if isinstance(c, dict) and c.get('type') == 'text'] if isinstance(cont, list) else []
                if isinstance(cont, list):
                    for c in cont:
                        if isinstance(c, dict) and c.get('type') == 'tool_result' and c.get('is_error'):
                            n_err += 1
                            txt = str(c.get('content', ''))[:60]
                            if 'denied' in txt.lower() or 'permission' in txt.lower():
                                agg['denials'] += 1
                            agg['errors'][txt] += 1
                for tx in texts:
                    tx = str(tx).strip()
                    if not tx:
                        continue
                    n_user += 1
                    if CORR.match(tx):
                        agg['corrections'].append(tx[:120])
                    if REJECT.search(tx):
                        agg['rejections'].append(tx[:120])
        ratio = reads / edits if edits else float(reads)
        agg['sessions'].append(dict(f=os.path.basename(f)[:16], reads=reads, edits=edits,
                                    ratio=round(ratio, 2), errs=n_err, user=n_user))
    return files, agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', type=int, default=40)
    ap.add_argument('--min-bytes', type=int, default=200_000)
    ap.add_argument('--project', default='')
    ap.add_argument('--json', default='')
    a = ap.parse_args()
    files, agg = mine(a.window, a.min_bytes, a.project)
    ratios = sorted(s['ratio'] for s in agg['sessions'])
    med = ratios[len(ratios) // 2] if ratios else 0
    out = dict(
        n_sessions=len(files),
        top_tools=agg['tools'].most_common(12),
        top_bash=agg['bash'].most_common(15),
        top_errors=[(e[:50], n) for e, n in agg['errors'].most_common(10)],
        skills=agg['skills'].most_common(12),
        denials=agg['denials'],
        median_read_edit=med,
        edit_first_sessions=sum(1 for r in ratios if r < 2),
        research_first_sessions=sum(1 for r in ratios if r >= 6),
        n_corrections=len(agg['corrections']),
        corrections_sample=agg['corrections'][:20],
        rejections_sample=agg['rejections'][:10],
        sessions=agg['sessions'],
    )
    if a.json:
        json.dump(out, open(a.json, 'w'), indent=1)
    view = {k: v for k, v in out.items() if k not in ('sessions', 'corrections_sample')}
    print(json.dumps(view, indent=1))
    print(f"\n{len(files)} sessions | median Read:Edit {med} | "
          f"{out['edit_first_sessions']} edit-first, {out['research_first_sessions']} research-first | "
          f"{out['n_corrections']} corrections, {out['denials']} denials")


if __name__ == '__main__':
    main()
