# Confusion matrix — gpt-5.4-nano-2026-03-17

| gold \ pred | reachable_vuln | safe | vacuous_noise | patched |
| --- | --- | --- | --- | --- |
| reachable_vuln | 8 | 0 | 0 | 0 |
| safe | 0 | 2 | 0 | 1 |
| vacuous_noise | 0 | 3 | 0 | 0 |
| patched | 1 | 0 | 0 | 7 |

## Failure taxonomy

- Vacuous vs Safe Confusion: 3
- Ignored Control / Patch Overclaim: 1
- Over-attributed Control: 1
