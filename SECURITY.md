# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in SkillGuard, **please do not open a public issue**. Instead, report it responsibly:

### Email (Preferred)
Send a detailed report to the maintainers (contact via GitHub Security Advisory system).

### GitHub Security Advisory
Use [GitHub's security advisory feature](https://github.com/ipriyaaanshu/agents/security/advisories) to report privately.

### What to Include
- Clear description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact and severity assessment
- Suggested fix (if you have one)
- Your contact information for follow-up

## Security Considerations

### Sandbox Model
- All skills run in Wasmtime WASI capability-based sandboxes
- Network, filesystem, and subprocess access is explicitly declared
- Permissions are checked at runtime; violations result in `SkillResult.denied()`

### Skill Trust Levels
```
Official (SkillGuard team)       ← Highest trust, fully audited
   ↓
Verified Publishers              ← Identity verified, cryptographically signed
   ↓
Community Publishers             ← Signed, community reviewed
   ↓
Unverified                       ← Use at own risk, max sandbox restrictions
```

### Permission Model
- **Network**: Allowlisted domains only (no DNS rebinding via IP); ports restricted
- **Filesystem**: Workspace-scoped paths only (no `/etc`, `/etc/passwd`, etc.)
- **Subprocess**: Allowlisted binaries only (e.g., `git` for git-local skill)
- **Environment**: Explicit, named variables (e.g., `GITHUB_TOKEN`, never `*`)

### What We Protect Against
✅ **Malicious Skill Code** — Sandbox enforcement, permission validation, capability restriction
✅ **Supply Chain Attacks** — Sigstore signing, reproducible builds, SLSA Level 3
✅ **Privilege Escalation** — Strict permission enforcement, no ambient authority
✅ **Data Exfiltration** — Network allowlists, filesystem scoping
✅ **Code Injection** — Parameterized queries, input validation

### Known Limitations
⚠️ **Compromised Host** — If your machine is already compromised, sandbox protections may not help
⚠️ **Shared Resources** — Shared systems may leak information between users via timing attacks
⚠️ **Transitive Trust** — A compromised upstream library still affects SkillGuard skills
⚠️ **Zero-Days** — Unknown vulnerabilities in Wasmtime or dependencies may exist

## Secure Coding Practices for Skill Authors

When writing new SkillGuard skills:

### ✅ DO:
- Use parameterized queries for all SQL operations
- Validate and sanitize all user inputs
- Check `context.dry_run` before side effects
- Use `SkillResult.denied()` for permission boundary violations
- Keep permissions minimal (principle of least privilege)
- Use `context.timeout_seconds` for long-running operations
- Prefer allowlists over blocklists for validation
- Handle errors gracefully without exposing sensitive data

### ❌ DON'T:
- Hardcode credentials (use environment variables or `context.secrets`)
- Use string concatenation for SQL/shell commands (parameterize)
- Trust filesystem paths without validation
- Request more permissions than necessary
- Catch all exceptions silently
- Log sensitive data
- Make assumptions about the sandbox (e.g., "I'm isolated, so it's OK to trust this string")

## Dependency Security

### Rust Dependencies
- Keep Cargo.toml dependencies updated
- Use `cargo audit` to check for known vulnerabilities
- Review dependency changes in PRs

### Python Dependencies
- Use `pip-audit` for vulnerability scanning
- Pin versions in skill `skillguard.yaml` build dependencies
- Test upgrades in sandboxed environments

## Audit & Disclosure
- Security issues are addressed with highest priority
- We follow a 90-day responsible disclosure period
- Fixed versions are released on a priority basis
- Public disclosure happens after patches are available

## Security Checklist for Skill Approval
- [ ] No hardcoded secrets or credentials
- [ ] Input validation present
- [ ] Parameterized queries (if SQL)
- [ ] Filesystem paths scoped to workspace
- [ ] Subprocess allowlist is specific (no wildcards)
- [ ] Network domains whitelisted (no `*`)
- [ ] Dry-run support implemented
- [ ] Error handling doesn't leak sensitive data
- [ ] Permission manifest is minimal and justified
- [ ] Code reviewed by at least one maintainer

## Security Advisories

We will publish security advisories for:
- Vulnerabilities in SkillGuard core (sandbox, CLI, registry)
- Vulnerabilities in official skills (skillguard-official namespace)
- Critical upstream vulnerabilities affecting multiple skills

Minor or upstream-only issues may be reported in CHANGELOG instead.

---

**Last Updated**: 2026-03-03
**Maintained By**: SkillGuard Security Team

Thank you for helping keep SkillGuard secure! 🔒
