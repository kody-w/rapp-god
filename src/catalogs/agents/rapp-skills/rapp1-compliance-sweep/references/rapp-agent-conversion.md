# Convert the Sweep into a RAPP Agent

`rapp-skills` is the portable Agent Skills staging area. Inside RAPP this
capability must become one single-file agent:

```text
rapp1_compliance_sweep_agent.py
```

The converted file must preserve the actual agent source and manifest. It
should contain:

1. input and result schemas;
2. the exact authority pin;
3. inventory and recursive archive logic;
4. role and mutability classification;
5. RAPP/1 requirement mappings;
6. safe checker/test orchestration;
7. ledger and issue serializers;
8. resume/idempotency state;
9. the public `perform()` entrypoint.

Do not leave core behavior in `SKILL.md` or make the RAPP runtime depend on
this directory. A Dataverse-native build must store the inspectable
`rapp1_compliance_sweep_agent.py` source and manifest in Dataverse.

Suggested tests:

1. exact authority bytes are required;
2. tracked-tree and ledger sets must be equal;
3. nested archives cannot escape their container;
4. immutable installer paths reject mutation;
5. structural success cannot imply authenticated acceptance;
6. blocked files prevent a complete verdict;
7. generated output requires provenance and deterministic regeneration;
8. duplicate issue filing is idempotent;
9. owner inputs remain null without independent evidence;
10. resume reuses only evidence from the same authority and target tree.
