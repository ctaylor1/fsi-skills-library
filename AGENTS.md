# Repository instructions

## Authorship and attribution

- Do not add authorship, contributor, coauthor, acknowledgment, signature, badge,
  promotional link, or generation credits for any AI assistant, model, vendor,
  coding tool, or automation service. This applies to source code, comments,
  documentation, generated artifacts, commit messages, and pull request text.
- This rule includes Claude, Anthropic, Codex, OpenAI, ChatGPT, Copilot, Gemini,
  Cursor, and every other AI tool or provider, including tools not listed here.
- Do not append coauthor trailers or tool-credit footers to commits or pull
  requests. Preserve the user's configured human author and committer identity.
- Preserve genuine third-party copyright and license notices. Accurate platform
  documentation, dependency names, model identifiers, and validation provenance
  are permitted when they describe functionality or evidence rather than credit
  a tool as a contributor to this repository.
- Enable the repository hooks in every clone with
  `git config --local core.hooksPath .githooks`. Do not bypass the hooks.
- Before committing, run `python3 tools/check_contributor_policy.py --staged`.
  Before pushing, check the complete branch history with
  `python3 tools/check_contributor_policy.py --history HEAD --tree`.
- Never merge an old branch merely to reconcile attribution-cleaned history:
  inspect it first, because that can restore removed contributor credits.
  Publishing rewritten shared history requires the user's explicit approval.
