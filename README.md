<div align="center">

# SkillGuard

**Chainguard for AI Agent Skills** — Secure, signed, and verified skills for any agent framework.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.75+-orange.svg)](https://rust-lang.org)
[![Security](https://img.shields.io/badge/security-first-red.svg)](#security)
[![Skills](https://img.shields.io/badge/skills-15-brightgreen.svg)](#official-skills-catalog)

[![GitHub stars](https://img.shields.io/github/stars/ipriyaaanshu/skillguard)](https://github.com/ipriyaaanshu/skillguard/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ipriyaaanshu/skillguard)](https://github.com/ipriyaaanshu/skillguard/network)
[![GitHub commits](https://img.shields.io/github/commit-activity/t/ipriyaaanshu/skillguard)](https://github.com/ipriyaaanshu/skillguard/graphs/commit-activity)
[![GitHub issues](https://img.shields.io/github/issues/ipriyaaanshu/skillguard)](https://github.com/ipriyaaanshu/skillguard/issues)
[![Last commit](https://img.shields.io/github/last-commit/ipriyaaanshu/skillguard)](https://github.com/ipriyaaanshu/skillguard/commits)

</div>

---

## The Problem

The AI agent ecosystem has a **supply chain security crisis**:

- **ClawHavoc (Feb 2026)**: 341 malicious skills stealing user data, 283 with critical flaws
- **MalTool Report**: 6,487 malicious tools evading detection across ecosystems
- **82.4%** of LLMs execute malicious commands from peer agents
- Existing marketplaces prioritize growth over security

Meanwhile, skills are **fragmented** across frameworks (OpenClaw, LangChain, CrewAI, AutoGPT) with no universal standard for secure distribution.

## The Solution

**SkillGuard** applies Chainguard's proven model to AI agent skills:

```
┌─────────────────────────────────────────────────────────────────┐
│                        SKILLGUARD                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   SKILL     │  │   BUILD     │  │   VERIFY    │              │
│  │   SOURCE    │──▶│   FACTORY   │──▶│   & SIGN    │──▶ REGISTRY │
│  │   (Git)     │  │  (Isolated) │  │  (Sigstore) │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────┐            │
│  │              CONTINUOUS SECURITY                 │            │
│  │  • Daily rebuilds from source                   │            │
│  │  • Automated CVE patching                       │            │
│  │  • Dependency graph analysis                    │            │
│  │  • Runtime behavior monitoring (WASI sandbox)   │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Core Principles

### 1. **Secure by Default**
- Skills run in Wasmtime WASI capability-based sandboxes
- Explicit permission manifests (like Android/iOS)
- No network/filesystem access unless declared and approved

### 2. **Cryptographic Trust**
- Every skill signed with Sigstore
- Reproducible builds with full provenance
- Verify before install, always

### 3. **Framework Agnostic**
- Works with OpenClaw, LangChain, CrewAI, AutoGPT, MCP
- Adapters for existing standards (Agent Skills, OSSA, OAF)
- Write once, run anywhere

### 4. **Continuous Security**
- Daily rebuilds from source (not just version bumps)
- Automated vulnerability scanning
- Instant revocation for compromised skills

---

## Architecture

The core runtime is implemented in **Rust** with Wasmtime for WASI sandboxing:

```
skillguard/
├── rust/                   # Core Rust implementation
│   └── crates/
│       ├── skillguard-core/      # Manifest parsing, skill types
│       ├── skillguard-sandbox/   # Wasmtime WASI sandbox runtime
│       ├── skillguard-signing/   # Sigstore integration
│       ├── skillguard-registry/  # Skill registry and resolution
│       └── skillguard-cli/       # Command-line interface
│
└── skills/                 # Official Verified Skills (15 total)
    ├── file-ops/           # ✅ Secure file operations
    ├── web-fetch/          # ✅ HTTP fetch and text extraction
    ├── github-mcp/         # ✅ GitHub API (repos, issues, PRs, search)
    ├── brave-search/       # ✅ Privacy-first web and news search
    ├── e2b-sandbox/        # ✅ Cloud code execution (Python/JS/Shell)
    ├── playwright-browser/ # ✅ Real browser automation
    ├── postgres-mcp/       # ✅ PostgreSQL database access
    ├── context7-docs/      # ✅ Live library documentation fetcher
    ├── git-local/          # ✅ Local git operations
    ├── firecrawl-scraper/  # ✅ Web-to-Markdown conversion
    ├── docker-mcp/         # ✅ Docker container management
    ├── memory-graph/       # ✅ Persistent knowledge graph memory
    ├── sqlite-mcp/         # ✅ Local SQLite database
    ├── slack-mcp/          # ✅ Slack workspace integration
    └── sentry-errors/      # ✅ Sentry error monitoring
```

---

## Official Skills Catalog

### Tier 1 — Essential (every coding agent needs these)

| Skill | Description | Permissions | Upstream |
|-------|-------------|-------------|----------|
| `file-ops` | Secure file read/write/search in workspace | filesystem:workspace | — |
| `web-fetch` | HTTP fetch, JSON, and text extraction | network:\* GET | — |
| `github-mcp` | Repos, issues, PRs, code search via GitHub API | network:api.github.com | [github/github-mcp-server](https://github.com/github/github-mcp-server) |
| `brave-search` | Privacy-first web and news search | network:api.search.brave.com | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search) |
| `e2b-sandbox` | Safe cloud code execution (Python/JS/Shell) in microVMs | network:api.e2b.dev | [e2b-dev/mcp-server](https://github.com/e2b-dev/mcp-server) |
| `playwright-browser` | Real browser automation via Chromium | network:\*, subprocess:chromium | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) |
| `postgres-mcp` | PostgreSQL queries and schema inspection | network:TCP to DB host | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres) |
| `context7-docs` | Fetch current library docs to prevent hallucinated APIs | network:context7.com | [upstash/context7](https://github.com/upstash/context7) |
| `git-local` | Local git operations (status, diff, log, commit, blame) | filesystem:workspace, subprocess:git | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/git) |

### Tier 2 — High Value (professional and team workflows)

| Skill | Description | Permissions | Upstream |
|-------|-------------|-------------|----------|
| `firecrawl-scraper` | Convert any URL to LLM-ready Markdown; crawl and extract | network:api.firecrawl.dev | [mendableai/firecrawl-mcp-server](https://github.com/mendableai/firecrawl-mcp-server) |
| `docker-mcp` | Container management — list, run, stop, logs, inspect | filesystem:/var/run/docker.sock, subprocess:docker | [docker/mcp-server](https://github.com/docker/mcp-server) |
| `memory-graph` | Persistent knowledge graph memory across agent sessions | filesystem:workspace/.skillguard/memory | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) |
| `sqlite-mcp` | Local SQLite database for prototyping and agent storage | filesystem:workspace | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite) |
| `slack-mcp` | Read/post Slack messages, search workspace history | network:slack.com, api.slack.com | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/slack) |
| `sentry-errors` | Full stack traces, breadcrumbs, and issue management | network:sentry.io | [mcp.sentry.dev](https://mcp.sentry.dev) |

---

## Skill Manifest

Every skill declares its permissions explicitly:

```yaml
# skillguard.yaml
name: github-mcp
version: 1.0.0
description: GitHub operations for AI agents
author: skillguard-official
license: Apache-2.0
upstream: https://github.com/github/github-mcp-server

# Explicit capability declarations
permissions:
  network:
    - domain: "api.github.com"
      methods: [GET, POST, PATCH]
      ports: [443]
  filesystem: []
  subprocess: false
  environment:
    - name: "GITHUB_TOKEN"
      required: true
      sensitive: true

# Framework compatibility
adapters:
  openclaw: ">=2.0"
  langchain: ">=0.3"
  mcp: ">=1.0"

# Build configuration
build:
  reproducible: true
  base: "skillguard/python:3.11-minimal"

# Security metadata
security:
  slsa_level: 3
```

---

## CLI Usage

```bash
# Install SkillGuard CLI (Rust binary)
cargo install skillguard

# Initialize a new skill project
skillguard init my-skill --template=basic

# Build with full verification
skillguard build --sign

# Verify a skill before installing
skillguard verify github-mcp@1.0.0

# Install a verified skill
skillguard install github-mcp

# Audit installed skills for vulnerabilities
skillguard audit

# Run a skill in sandbox (for testing)
skillguard run github-mcp --action=list-issues --repo=owner/repo

# Publish to registry (requires identity verification)
skillguard publish --sign
```

---

## Security Model

### Permission Levels

| Level | Network | Filesystem | Subprocess | Example Skills |
|-------|---------|------------|------------|----------------|
| **Minimal** | None | None | No | memory-graph, sqlite-mcp |
| **Restricted** | Allowlist only | Workspace only | No | github-mcp, brave-search, postgres-mcp |
| **Standard** | Allowlist only | Workspace + temp | Allowlist | git-local (git only), playwright-browser |
| **Privileged** | Any | Any | Yes | docker-mcp (Docker socket + CLI) |

### Trust Hierarchy

```
┌─────────────────────────────────────────┐
│           SKILLGUARD OFFICIAL           │  ← Maintained by core team
│         (Highest trust, audited)        │
├─────────────────────────────────────────┤
│           VERIFIED PUBLISHERS           │  ← Identity verified, signed
│         (High trust, monitored)         │
├─────────────────────────────────────────┤
│          COMMUNITY PUBLISHERS           │  ← Signed, community reviewed
│         (Medium trust, sandboxed)       │
├─────────────────────────────────────────┤
│             UNVERIFIED                  │  ← Use at own risk
│         (Low trust, max sandbox)        │
└─────────────────────────────────────────┘
```

### Supply Chain Security (SLSA Level 3)

- **Source**: Verified git commits with signed tags
- **Build**: Isolated, reproducible builds via Rust/Wasmtime
- **Provenance**: Full build attestation via Sigstore
- **Distribution**: Signed artifacts with cryptographic verification

---

## Framework Adapters

SkillGuard skills work everywhere:

```python
# Use with OpenClaw
from skillguard.adapters import openclaw
skill = openclaw.load("github-mcp")

# Use with LangChain
from skillguard.adapters import langchain
tool = langchain.as_tool("github-mcp")

# Use with CrewAI
from skillguard.adapters import crewai
crewai_tool = crewai.as_tool("github-mcp")

# Use with MCP
from skillguard.adapters import mcp
mcp_server = mcp.as_server("github-mcp")
```

---

## Roadmap

### Phase 1: Foundation (Current)
- [x] Rust core with Wasmtime WASI sandbox runtime
- [x] Skill manifest schema (`skillguard.yaml`)
- [x] 15 official verified skills (Tier 1 + Tier 2)
- [x] Upstream skill migration from top MCP/ClawHub sources
- [ ] CLI for init, build, verify, install (`skillguard-cli` — in progress)
- [ ] Sigstore signing integration
- [ ] OpenClaw + LangChain adapters

### Phase 2: Registry & Distribution
- [ ] Decentralized registry (Git-based)
- [ ] Dependency resolution with SAT solver
- [ ] Mirror network for availability
- [ ] CVE database integration

### Phase 3: Continuous Security
- [ ] Daily automated rebuilds
- [ ] Runtime behavior monitoring
- [ ] Anomaly detection
- [ ] Instant revocation system

### Phase 4: Ecosystem
- [ ] Web UI for browsing skills
- [ ] Publisher verification program
- [ ] Security audit partnerships
- [ ] Enterprise features (SSO, private registries)

---

## Comparison

| Feature | ClawHub | Agent Skills | SkillFortify | **SkillGuard** |
|---------|---------|--------------|--------------|----------------|
| Framework agnostic | ❌ | ✅ | ❌ | ✅ |
| Cryptographic signing | ❌ | ❌ | ❌ | ✅ |
| Reproducible builds | ❌ | ❌ | ❌ | ✅ |
| Permission manifests | Basic | ❌ | ✅ | ✅ |
| Capability sandbox | ❌ | ❌ | ✅ | ✅ (WASI) |
| Continuous rebuilds | ❌ | ❌ | ❌ | ✅ |
| SLSA compliance | ❌ | ❌ | ❌ | ✅ |
| Official skill catalog | ✅ | ✅ | ❌ | ✅ (15 skills) |
| Production ready | ✅ | ✅ | ❌ | 🚧 |

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repo
git clone https://github.com/ipriyaaanshu/skillguard.git
cd skillguard

# Build the Rust core
cd rust && cargo build

# Run Rust tests
cargo test

# Run linting
cargo clippy
```

### Adding a New Skill

1. Create `skills/<skill-name>/skillguard.yaml` with permission manifest
2. Create `skills/<skill-name>/skill.py` implementing the `Skill` base class
3. Create `skills/<skill-name>/__init__.py` exporting `create_skill`
4. Submit a PR — security review is required for any new permission scopes

---

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Chainguard](https://chainguard.dev) - Inspiration for supply chain security model
- [Sigstore](https://sigstore.dev) - Cryptographic signing infrastructure
- [SLSA](https://slsa.dev) - Supply chain security framework
- [Wasmtime](https://wasmtime.dev) - WASI sandbox runtime
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) - Reference MCP server implementations
- [github/github-mcp-server](https://github.com/github/github-mcp-server) - GitHub official MCP server
- [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) - Playwright browser automation
- [mendableai/firecrawl-mcp-server](https://github.com/mendableai/firecrawl-mcp-server) - Firecrawl web scraping
- [e2b-dev/mcp-server](https://github.com/e2b-dev/mcp-server) - E2B cloud sandbox
- [upstash/context7](https://github.com/upstash/context7) - Live documentation fetching
- [Agent Skills](https://agentskills.io) - Skill format inspiration
- [OSSA](https://openstandardagents.org) - Agent specification work

---

<p align="center">
  <b>Secure skills for a safer agentic future.</b>
</p>
