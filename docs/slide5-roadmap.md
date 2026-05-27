# Slide 5 — Roadmap (deck copy, draft 2026-05-27)

**LeakGuard watches every surface AI-assisted development can leak a credential through.**

1. **Today (v1) — Detection.** We watch the public web — paste sites, screenshot mirrors,
   gist and AI-transcript leaks — and verify real exposures with a two-LLM Analyst–Judge.
   Powered by Bright Data, the only way to watch the open web reliably at scale.
2. **Next — upstream to the source.** The same Analyst–Judge brain moves to where AI builders
   actually leak: the AI prompt, the pre-commit, the pull request — catching credentials
   *before* they ever reach the public web.
3. **The moat — one cross-surface defense, compounding.** Detection stays the permanent
   backstop (prevention is never 100%), and every verified leak sharpens the rubric across all
   surfaces. Git-only tools and regex hooks can't match a brain that reasons about context
   everywhere a key can escape.

> Honesty guardrail for the deck: v1 (detection, one identity, mock paste sites) is what's
> *built*. Slide 5 is the vision — phrase it as direction, don't imply it's shipped.
