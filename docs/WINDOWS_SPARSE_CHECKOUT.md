# Windows checkout policy

The exact public imports include 28 paths that Windows cannot materialize and
five paths at or above the traditional 260-byte limit. They are preserved
without renaming in `catalog/portability.json`.

Use a no-checkout clone and sparse checkout on native Windows:

```powershell
git clone --no-checkout https://github.com/kody-w/rapp-god.git
cd rapp-god
git sparse-checkout init --cone
git sparse-checkout set authority vendor src services integrations docs compat catalog provenance tests tools
git checkout
```

That profile intentionally omits product instance state. Use WSL or a
case-sensitive Linux filesystem when the complete Rappterbook evidence tree is
required. Enabling `core.longpaths` does not make control characters legal, so
it is not a complete substitute for sparse checkout.
