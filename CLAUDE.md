# ka-subs-creator

Makes Georgian `.srt` subtitles for Khan Academy YouTube videos that have none:
audio → Gemini writes the words → forced alignment gives every word its time → `.srt` → checks.

**Read `PLAN.md` before doing anything.** It's the full build guide and carries what's already
proven (don't re-test that) and what's still an open question.

## Rules

- **The owner is a non-developer.** Explain changes as what and why, in plain language. Ask the
  questions in PLAN.md §1 before building, and stop for the owner's review after each step in §5.
- **Windows PC.** Give install and run steps as copy-pasteable commands, one per block.
- **The owner handles git.** Don't commit or push unless asked in that conversation.
- **Never commit secrets.** The Gemini key lives only in `.env` (git-ignored); `.env.example`
  has the name.
- **Free only.** No paid services; Gemini's free tier is small, so treat each call as scarce.
- **One feature per file.** Small modules over one big script.
