# Confusion matrix — claude-sonnet-4-5-20250929

| gold \ pred | reachable_vuln | safe | vacuous_noise | patched |
| --- | --- | --- | --- | --- |
| reachable_vuln | 8 | 0 | 0 | 0 |
| safe | 0 | 3 | 0 | 0 |
| vacuous_noise | 0 | 0 | 3 | 0 |
| patched | 1 | 0 | 0 | 7 |

## Failure taxonomy

- Ignored Control / Patch Overclaim: 1
