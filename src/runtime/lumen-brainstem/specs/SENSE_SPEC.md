# SENSE_SPEC — `rapp-sense/1.0`

> **Frozen excerpt** of the canonical sense contract. Bundled at planting time on 2026-05-09T15:45:28Z.

A **sense** is an ambient on-each-turn suggestion engine. It rides the LLM's reply — appended after a delimiter — and produces a parallel artifact (a translation, a suggestion, an emoji summary, a creative prompt). Frontends consume the side channel; the main reply stays clean.

## Where senses live

The canonical store is [`kody-w/RAPP_Sense_Store`](https://github.com/kody-w/RAPP_Sense_Store). This neighborhood can ALSO host its own senses under `senses/<publisher>/<id>_sense.py` — neighborhood-specific senses (e.g. an art-collective's `critique_sense` that suggests next remixes; a braintrust's `cite-find_sense` that suggests citation gaps).

## File contract (single file, single module)

```python
"""<NAME> — <one-line description>.

<Longer description: what this sense produces, why it exists.>
"""

name = "<short-name>"                   # stable identifier
delimiter = "|||<NAME>|||"              # appears between main reply and the sense's output
response_key = "<name>_response"        # JSON field for frontends
wrapper_tag = "<name>"                  # HTML tag for inline rendering
system_prompt = (
    "After your main reply, append `|||<NAME>|||` followed by "
    "<what the sense should produce>. Always emit — empty is not allowed."
)

__manifest__ = {
    "schema":      "rapp-sense/1.0",
    "name":        "@<publisher>/<short-name>",
    "version":     "0.1.0",
    "description": "<one-line>",
}
```

## How the brainstem uses senses

On each `/chat` turn, the brainstem:
1. Concatenates active senses' `system_prompt` into the system prompt.
2. The LLM emits the main reply + each sense's delimiter + its content.
3. The brainstem splits on each delimiter, stores the side channel in `<response_key>`.
4. Frontends render the main reply + any sense channels they care about.

## Multiple senses compose

If you have `eli5_sense` + `emoji_sense` + `spark_sense` all loaded, the response has 3 side channels. Each delimiter is unique; order doesn't matter; senses don't interact.

## Neighborhood-local senses

This neighborhood can ship its OWN senses for participants who subscribe. Examples that fit the kind:

- **ant-farm:** `next_topic_sense` — suggests the colony task with lowest pheromone count
- **art-collective:** `critique_sense` — appends a 2-sentence aesthetic note about the recent submission
- **braintrust:** `cite_find_sense` — appends a candidate citation the contributor missed
- **workspace:** `next_action_sense` — appends "the next workspace-todo I'd pick if I were you"
- **twin:** `voice_drift_sense` — flags when the twin's reply drifted from soul.md voice

## Hard rules

- **Decoupled by design.** A sense NEVER auto-feeds its output into another agent. Operator agency is the whole point.
- **Always emit.** Empty side channels confuse frontends. If nothing meaningful, emit a placeholder and explain.
- **No self-reference.** A sense should not analyze ITSELF or critique its own delimiter. Keep them independent.
- **Don't drift the main reply.** The sense system prompt should not influence what the main reply IS — only what gets appended after.

---

*Schema: `rapp-sense/1.0`. Canonical store: kody-w/RAPP_Sense_Store. Local store (this neighborhood): `senses/`.*
