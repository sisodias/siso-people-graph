# Red-team source archive

This directory preserves the user-provided program prompt bundle and the exact
Prompt 2 slice used to define the forensic red-team lane. It exists so future
agents can audit scope and acceptance criteria without relying on chat history.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `parallel-slam-gpt-5.6-agent-prompts-2026-08-06.txt` | 54730 | `077e5096298b776b5df33aba7ac8fa159296b3671c570a92a64ad74ebe53674d` |
| `prompt-02-people-graph-red-team.txt` | 3353 | `5f490d41ebe26f768131ec9d1f08b8ba6c0736a316ed4336250a104a48298f00` |

The full provenance and code-source pins are in
`docs/audits/people-graph-v2-source-manifest.json`.


A machine-readable interpretation of Prompt 2 is stored at
`tests/red_team/fixtures/prompt_2_contract.json`. The text files in this
directory remain authoritative; the JSON contract is validated against their
SHA-256 digests and exists only to support automated traceability checks.
