# Changelog

All notable changes to SkillGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **15 Official Verified Skills** — Complete Tier 1 & 2 skill catalog:
  - **Tier 1** (Essential): github-mcp, brave-search, e2b-sandbox, playwright-browser, postgres-mcp, context7-docs, git-local
  - **Tier 2** (High Value): firecrawl-scraper, docker-mcp, memory-graph, sqlite-mcp, slack-mcp, sentry-errors
  - Plus existing file-ops and web-fetch skills
- **Comprehensive Permission Manifests** — All 15 skills include `skillguard.yaml` with explicit network allowlists, filesystem scoping, subprocess restrictions
- **Updated README** — Full skills catalog, security model, framework adapters, updated roadmap
- **Upstream Skill Migration** — Ported top trending skills from:
  - modelcontextprotocol/servers (7 official MCP reference implementations)
  - github/github-mcp-server (15.2k⭐)
  - microsoft/playwright-mcp (Microsoft official)
  - mendableai/firecrawl-mcp-server (85k⭐)
  - e2b-dev/mcp-server, docker/mcp-server, upstash/context7

### In Progress
- Rust CLI implementation (skillguard-cli crate)
- Sigstore integration for cryptographic signing
- Framework adapters (OpenClaw, LangChain, MCP)

## [0.1.0] - 2026-02-28

### Added
- **Rust Core Implementation** — Wasmtime WASI sandbox runtime
  - skillguard-core: Manifest parsing and skill types
  - skillguard-sandbox: WASI capability-based execution
  - skillguard-signing: Sigstore integration layer
  - skillguard-registry: Registry and dependency resolution
  - skillguard-cli: Command-line interface foundation
- **Initial Skill SDK** — Python-based skill implementations
  - 2 official verified skills: file-ops, web-fetch
  - Permission manifest schema (skillguard.yaml)
  - Skill context and execution model
- **Security Foundation**
  - SLSA Level 3 compliant build process
  - Reproducible builds via Rust
  - Path traversal and sandbox boundary checks
  - Parameterized queries (SQL injection prevention)
- **GitHub Templates**
  - Bug report template with environment context
  - Feature request template with skill proposal section
  - Pull request template with security checklist
  - CI/CD workflows (Rust testing, linting, release)
- **Documentation**
  - README with architecture and security model
  - CONTRIBUTING.md with development setup
  - Apache 2.0 license

### Limitations
- CLI not yet fully implemented
- Sigstore signing pending
- No live registry yet (Git-based registry planned)
- Framework adapters pending

---

## Principles

We use the following conventions in this changelog:

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes and security improvements
- **Performance** for performance improvements

## Future

See the [Roadmap](README.md#roadmap) in the main README for upcoming features including:
- Phase 2: Decentralized registry and mirror network
- Phase 3: Continuous security with daily rebuilds and anomaly detection
- Phase 4: Enterprise features and web UI
