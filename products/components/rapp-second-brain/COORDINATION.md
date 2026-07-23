# COORDINATION — many Opuses, one brain, zero clobbering

Multiple Opus sessions crawl this brain in parallel. The design makes that
safe by construction. Follow this protocol exactly.

## The three rules that prevent all conflicts

1. **One card = one file.** `brain/cards/<id>.json`. You only ever create or
   overwrite cards for nodes YOU claimed. New files from different writers
   merge without conflict — git only fights over the *same* file.
2. **Never hand-edit `brain/INDEX.md` or `brain/graph.json`.** They are
   DERIVED. CI (`.github/workflows/reduce.yml`) rebuilds them from `cards/`
   on every push. Writers touching them = the one guaranteed conflict; so
   writers never touch them. If you need the graph, read it; to change it,
   change a card.
3. **Claim before you crawl.** `tools/claim.sh <id>` takes an atomic,
   git-enforced claim. If it says TAKEN, pick another node. This is how two
   Opuses avoid crawling the same repo.

## Your loop as a parallel writer

```bash
git pull --rebase --autostash                 # start fresh
tools/claim.sh repo:kody-w/rapp-canary        # atomic; skip node if TAKEN
#   … crawl the node, build the card JSON …
tools/save-card.sh brain/cards/repo_kody-w_rapp-canary.json   # write + pull-rebase + push, retried
```

`save-card.sh` and `claim.sh` both do pull-rebase-push with bounded retry, so
transient races self-heal. Because cards and claims are per-node files, a
rebase almost never conflicts; if it ever does, it's two writers on the SAME
node — meaning a claim was skipped. Don't skip claims.

## Sharding (optional, reduces even claim contention)

If N Opuses are running, shard the work up front instead of racing claims:
each takes repos where `sha1(name) % N == my_index`. `tools/shard.sh <N> <i>`
prints your slice. Claims still run as a backstop.

## Stale claims

A claim older than 6h with no card produced is presumed abandoned —
`tools/claim.sh --steal <id>` reclaims it (records the steal in the claim
file's history). Don't steal fresh claims.

## The private hemisphere uses the same machinery

`rapp-second-brain-private` carries identical `tools/` and the reducer. The
only difference is the source allowlist and that it never goes public.
