---
name: harvest
description: Distill a finished project from the Obsidian vault into a wiki article and cross-link it
---

# /harvest — distill a finished project into the wiki

Vault: `~/Documents/Obsidian Vault` (read its `CLAUDE.md` for full conventions before writing anything).

Argument: `$ARGUMENTS` — the project to harvest. May be a filename in `projects/`, a partial name, or empty.

## Steps

1. **Resolve the project file.** Look in `projects/` for a file matching `$ARGUMENTS` (fuzzy match on filename is fine). If no argument was given, list files in `projects/` with `status: done` (or `abandoned`) that have no `Harvested:` line, and ask which one to harvest. If the match is ambiguous, ask.

2. **Gate on status.** Only projects with `status: done` or `status: abandoned` may be harvested — the whole point of the wiki is that articles trace back to finished work. If the project is still `active` or `paused`, ask whether the user wants to close it first (and if yes, set `status: done` before continuing). Never silently harvest an active project.

3. **Gather the full story.** Read the entire project file, plus any `output/` artifacts it links to or that reference it (`grep -rF` for the project name across the vault). The article should be grounded in what actually happened, not what was planned.

4. **Distill — do not summarize.** Write the wiki article as the reusable lesson, stripped of project-specific narrative:
   - What is the transferable pattern, principle, or pipeline?
   - When does it apply, and when does it NOT apply?
   - What would you do differently next time? (failed approaches are often the most valuable part)
   - Concrete anchors: one or two short examples from the project, kept brief
   A reader should be able to apply the article to a new situation without ever opening the source project. If the project taught more than one distinct lesson, write multiple small articles rather than one grab-bag.

5. **Create the article(s)** in `wiki/` — plain markdown, no plugin syntax, no emojis:

   ```markdown
   ---
   created: <today YYYY-MM-DD>
   tags: [relevant, kebab-case, tags]
   harvested_from: "[[<Project Filename>]]"
   ---

   # <Pattern-style title — name the lesson, not the project>

   <article body>

   ## Related

   - [[<Project Filename>]] (source project)
   - [[<output artifacts, related wiki articles>]]
   ```

   Check `wiki/` for an existing article covering the same ground first — if one exists, update and extend it (append to its `harvested_from`) instead of creating a near-duplicate.

6. **Cross-link both directions.** In the project file, add under the title (or in a closing section):
   `Harvested: [[<Wiki Article Title>]] (<date>)`
   Link the new article from any obviously related wiki articles.

7. **Update the maps.** Add the article to `wiki/_index.md`; update the project's line in `projects/_index.md` (status done, harvested).

8. **Commit** in the vault repo: `harvest: <lesson> from <project>`.

9. **Report** back: article title(s), the one-sentence lesson each captures, and the links created.
