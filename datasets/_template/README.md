Template for onboarding a new dataset -- not a real dataset itself (`--all` skips any
`datasets/<id>/` folder whose name starts with `_`).

To use it:

```
cp -r datasets/_template datasets/<your_program_id>
```

Then edit `datasets/<your_program_id>/summary.md`'s front matter: set `program_id` to your
actual id, and `habitat`/`description` if you know them yet. See the top-level README's "Quick
start" section for what happens next.

`transform_notes.md` and `archive_summary.md` don't need editing yet -- their bodies get drafted
later, grounded in data the pipeline produces on its first run. They're included here only so
you can see what a brand-new dataset's docs look like before anything's been run.
