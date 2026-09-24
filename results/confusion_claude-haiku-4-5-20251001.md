# Confusion matrix — claude-haiku-4-5-20251001

| gold \ pred | reachable_vuln | safe | vacuous_noise | patched |
| --- | --- | --- | --- | --- |
| reachable_vuln | 8 | 0 | 0 | 0 |
| safe | 0 | 3 | 0 | 0 |
| vacuous_noise | 0 | 0 | 3 | 0 |
| patched | 3 | 0 | 0 | 5 |

## Failure taxonomy

- Ignored Control / Patch Overclaim: 3
