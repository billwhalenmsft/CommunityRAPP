# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main branch | ✅ Active |

## Reporting a Vulnerability

**Do not open a public GitHub Issue for security vulnerabilities.**

Report security issues privately via [GitHub Security Advisories](https://github.com/billwhalenmsft/CommunityRAPP-BillWhalen/security/advisories/new) or email the repo owner directly.

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if known)

We aim to respond within **48 hours** and resolve critical issues within **7 days**.

## Security Notes for This Repo

- `local.settings.json` is gitignored and must **never** be committed — it contains Azure keys
- All secrets must be stored as GitHub Actions secrets or Azure Key Vault references
- The default GUID `c0p110t0-aaaa-bbbb-cccc-123456789abc` is an intentional guardrail — see CLAUDE.md
- PATs stored in the CoE web UI are browser-localStorage only — never transmitted to any server except `api.github.com`
- Azure Function endpoints should use function-level auth keys, not anonymous auth, in production
