# Pre-public checklist

> ⚠️ **READ THIS FIRST — do not create new exposure while checking for it.**
> Never paste your personal identifiers (phone, home city, email, real name, travel details)
> into a chat or AI prompt to "have something grep them." Handing sensitive data to an AI tool
> is the exact pattern that leaks data in the first place. Put the list in a **gitignored local
> file** (`identifiers.local`) and run the search against that file. The check must never become
> the leak.

Run all three passes before flipping the repo to public. They are complementary, not
redundant — repeating one scan just repeats its blind spots. Layer different *types* of check.

## Pass 1 — Deterministic tool (structured secrets)
- [ ] Scan the **full git history**, not just the working tree: `gitleaks detect --redact`
      (or equivalent). Catches AWS / Stripe / GitHub / JWT / Slack patterns deterministically.
- [ ] Confirm the detect-secrets pre-commit hook is installed and the baseline is current.
- [ ] Fix anything that surfaces before continuing.

## Pass 2 — Named-target search (your specific data)
- [ ] List every identifier in `identifiers.local` (gitignored): full name, every email,
      phone, home city, LinkedIn handle, any client/project codename, any travel detail.
- [ ] Grep every term across **all files and commit messages**. Verifiable: each term either
      appears or it does not.
- [ ] Any remaining hit must be something you *chose* to publish (e.g. your author byline).

## Pass 3 — Human eyeball (context only you have)
- [ ] Open the repo on GitHub (still private) and read it like a stranger: README, commit
      messages, file names, `docs/`.
- [ ] Look for contextual leaks no tool or AI can flag: codenames, tone in a commit message,
      a function or branch named after a person or company.

## Then
- [ ] All three clean → flip to public.

~20 minutes. Far higher confidence than "an AI scan said it looked fine."
