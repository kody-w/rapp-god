# Authority

Machine-readable records in [`records/`](records/) define the authority order:

1. the unmodified RAPP/1 rev-5 structural pin;
2. the RAPP governance source commit for ratification, lifecycle, and
   unresolved owner decisions; its content is withheld and therefore fails
   closed (it is not technical protocol);
3. the immutable `rapp-installer@brainstem-v0.6.9` LTS grail;
4. target-owned adapters and migration controls;
5. imported implementations;
6. generated catalogs and observatories.

The RAPP/1 pin is structural evidence, not authenticated acceptance under
section 13. The imported RAPP baseline remains **NOT YET FULLY RAPP/1
CONFORMANT**. No target automation may manufacture keys, signatures, registry
freshness, an invite, or a re-anchor to change that status.

Exact upstream artifacts are isolated below `authority/protocol/`; target-owned
records never modify those bytes. The LTS grail is isolated under
`vendor/grail/`. Run `python3 tools/check_assimilation.py` to enforce both
boundaries offline.
