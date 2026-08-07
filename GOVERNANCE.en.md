# huaweicloud Open Source Governance Policy

> **Language:** English | [中文](./GOVERNANCE.md)
>
> Version: v1.0
> Effective date: 2026-08-03
> Scope: All repositories under the huaweicloud GitHub organization
> Author: Hermes Agent
> Approval: Pending TMG review

---

## Table of Contents

1. [General Provisions](#1-general-provisions)
2. [Three-Tier Admission System](#2-three-tier-admission-system)
3. [Repository Creation Standards](#3-repository-creation-standards)
4. [Maintenance & Operations Requirements](#4-maintenance--operations-requirements)
5. [Exit & Archival Mechanism](#5-exit--archival-mechanism)
6. [Roles & Responsibilities](#6-roles--responsibilities)
7. [Compliance Checks & Metrics](#7-compliance-checks--metrics)
8. [Appendix](#8-appendix)

---

## 1. General Provisions

### 1.1 Purpose

This policy establishes unified governance standards for all repositories in the huaweicloud GitHub organization, ensuring legal compliance, security, and community health of open source projects.

### 1.2 Scope

- All **public repositories** under this organization
- Private repositories follow with reference (except clauses limited by Free plan)
- Archived repositories are only subject to exit standards

### 1.3 Core Principles

1. **Legality first** — License is the first door to open source. Code without a license retains all rights legally, and others cannot legally use, modify, or distribute it. All public repositories in this organization must have an OSI-approved LICENSE file.

2. **Security is non-negotiable** — Branch protection, dependency scanning, and security vulnerability reporting channels are not optional. Projects with stars have users; with users comes security responsibility.

3. **Discoverability determines community size** — Repository description, Topics tags, and README determine whether users can find you on GitHub. If they can't find it, they won't use it; if they don't use it, they won't contribute.

4. **Gradual rather than shock** — Governance standards are implemented by repository influence tier, not one-size-fits-all.

5. **Open by default** — Repositories default to public, Issues enabled by default, Discussion encouraged. Unless there is a clear confidentiality need, information should be open and transparent.

### 1.4 Terminology

| Term | Definition |
|------|-----------|
| **Active repository** | A repository that is not archived |
| **Core repository** | Repository with Stars ≥ 50 |
| **Notable repository** | Repository with Stars ≥ 20 |
| **Zombie repository** | Repository with no git push for 365 consecutive days |
| **Single-maintainer repository** | Repository with only 1 write-permission member |
| **OSI-approved license** | A license in the OSI-approved open source license list |

---

## 2. Three-Tier Admission System

Repositories are divided into three tiers by influence (Stars), with progressively higher governance requirements.

### 2.1 Tier Division

| Tier | Criterion | Repo Count | Governance Intensity |
|:----:|-----------|:-------:|:--------:|
| **L1 Admission** | All active repositories | 155 | Legal baseline + discoverability |
| **L2 Healthy** | Stars ≥ 20 | 38 | L1 + security baseline + community participation |
| **L3 Benchmark** | Stars ≥ 50 | 17 | L2 + engineering excellence + community operations |

### 2.2 L1 — Admission Threshold (all active repositories must satisfy)

| No. | Check | Requirement | Severity |
|:----:|--------|------|:--------:|
| L1-1 | LICENSE | OSI-approved LICENSE file at root, Apache-2.0 recommended | **Blocking** |
| L1-2 | README.md | Contains project intro, installation, basic usage example | **Blocking** |
| L1-3 | Description | GitHub Description field non-empty | **Warning** |
| L1-4 | Default branch | Must be `main` | **Warning** |
| L1-5 | Issues enabled | `has_issues=true` | **Blocking** |
| L1-6 | Not archived | `archived=false` | — |
| L1-7 | Topics tags | At least 3 Topics tags (each matching `[a-z0-9][a-z0-9.-]*`) | **Blocking** |
| L1-8 | Issue labels | Must include `type/*`, `priority/*`, `status/*` labels (required by automation) | **Blocking** |

> **Blocking**: repository should not exist in the organization if not satisfied.
> **Warning**: must be remediated within 30 days.
> **Suggestion**: encouraged, not mandatory.

### 2.3 L2 — Health Baseline (repositories with Stars ≥ 20 must satisfy)

In addition to L1:

| No. | Check | Requirement | Severity |
|:----:|--------|------|:--------:|
| L2-1 | Branch protection | require PR + ≥2 reviews + dismiss stale reviews | **Blocking** |
| L2-2 | Contributor redundancy | ≥2 write-permission members | **Blocking** |
| L2-3 | SECURITY.md | Security vulnerability reporting policy file exists | **Blocking** |
| L2-4 | CONTRIBUTING.md | Contribution guide file exists | **Blocking** |
| L2-5 | CODE_OF_CONDUCT.md | Code of conduct file exists | **Warning** |
| L2-6 | Dependabot | Dependabot alerts + security updates enabled | **Blocking** |
| L2-7 | PR Template | Pull Request template exists | **Warning** |
| L2-8 | Issue Template | Bug Report + Feature Request templates exist | Suggestion |

### 2.4 L3 — Benchmark (repositories with Stars ≥ 50 should satisfy)

In addition to L2:

| No. | Check | Requirement | Severity |
|:----:|--------|------|:--------:|
| L3-1 | CI/CD | lint + test automation workflows | **Blocking** |
| L3-2 | CodeQL | Code security scanning enabled | **Blocking** |
| L3-3 | Issue response SLA | First response ≤7 days, close ≤90 days | **Warning** |
| L3-4 | SemVer | Versioning follows semantic versioning | **Warning** |
| L3-5 | Changelog | CHANGELOG.md or Release Notes exists | Suggestion |
| L3-6 | Discussions | GitHub Discussions enabled | Suggestion |
| L3-7 | good-first-issue | At least 1 Issue suitable for new contributors | Suggestion |

---

## 3. Repository Creation Standards

> **Detailed creation process: see [Repository Creation Process](./docs/建仓流程文档.en.md)** — this chapter only lists key points.

### 3.1 New Repository Workflow

```
Repo request → Review → Create → Initialize → Acceptance
```

### 3.2 Auto-Config Checklist on Creation

New repositories should automatically include the following configs (auto-injected by the creation process `repo_creator.py`):

- [ ] Apache-2.0 LICENSE file
- [ ] README.md (project intro + installation + quick start)
- [ ] .github/ISSUE_TEMPLATE/bug_report.yml
- [ ] .github/ISSUE_TEMPLATE/feature_request.yml
- [ ] .github/ISSUE_TEMPLATE/config.yml
- [ ] .github/PULL_REQUEST_TEMPLATE.md
- [ ] .github/CODEOWNERS (auto-assign PR reviewers)
- [ ] .github/dependabot.yml
- [ ] .github/workflows/ci.yml (CI: lint → test → build)
- [ ] .github/workflows/triage-issue.yml (product tier)
- [ ] .github/workflows/status-transition.yml (product tier)
- [ ] .github/workflows/sync-to-gitcode.yml (product tier)
- [ ] Security alerts + automated fixes (Dependabot alerts/fixes)
- [ ] Repository-level Secrets (BOT_TOKEN / GITCODE_TOKEN, for triage / GitCode sync)
- [ ] Branch protection (public repos only: 2 Approvals + Code Owner Review + strict CI)
- [ ] Repository description
- [ ] At least 3 Topics tags (required)
- [ ] Default branch `main`
- [ ] Issues enabled
- [ ] Squash merge enabled (default)

### 3.3 Naming Conventions

- Use lowercase letters + hyphens: `huaweicloud-sdk-python-v3`
- Avoid conflicts with existing repository names
- SDK naming: `huaweicloud-sdk-{language}-{variant}`
- IoT naming: `huaweicloud-iot-{category}-sdk-{language}`
- Tool/plugin naming: `{function}-{platform}`

### 3.4 Visibility Selection

| Scenario | Recommended Visibility |
|----------|:----------:|
| SDK, tools, sample code | public |
| Internal docs, configs | private |
| Experimental projects | public (marked experimental) |
| Contains sensitive info | private |

---

## 4. Maintenance & Operations Requirements

### 4.1 Repository Maintainer Responsibilities

1. **Issue response**: first response to new Issues within 7 days
2. **PR Review**: complete PR review within 14 days
3. **Security vulnerabilities**: handle per SLA in SECURITY.md
4. **Dependency updates**: merge or close Dependabot PRs within 30 days
5. **Quarterly checks**: verify L1/L2 compliance status quarterly

### 4.2 Community Operations Requirements (L3 repositories)

1. **good-first-issue**: always keep at least 1 Issue suitable for new contributors
2. **Contributor recognition**: acknowledge contributors in README or CONTRIBUTORS.md
3. **Release notes**: every Release includes Changelog
4. **Breaking change notice**: announce breaking changes at least 30 days in advance

### 4.3 License Requirements

| Project Type | License |
|----------|--------|
| SDK / Library | Apache-2.0 |
| Tool / CLI | Apache-2.0 or MIT |
| Sample / Demo | Apache-2.0 |
| Docs / Dataset | Forced Apache-2.0 |
| Internal config | Forced Apache-2.0 |

> **License policy is consistent with the creation process**: only Product projects (SDK/Action/Provider/Framework/Exporter/IoT) allow user choice (Apache-2.0 / MIT / BSD-3-Clause); samples/docs/internal are uniformly forced to Apache-2.0. See [Repository Creation Process §3.5](./docs/建仓流程文档.en.md).
> CC-BY-4.0 may be used for standalone dataset repositories (not created via the creation process), subject to organization admin approval.

**GPL usage restriction:** GPL code must not be mixed into Apache-2.0 projects unless legal review confirms license compatibility. Existing GPL repositories need individual license migration assessment.

---

## 5. Exit & Archival Mechanism

### 5.1 Archival Conditions

Archival should be initiated if **any** of the following is met:

| Condition | Description |
|------|------|
| No git push for 365 consecutive days | May have stopped maintenance |
| Maintainer confirms stopping maintenance | Voluntary declaration |
| Superseded by another repository | Feature merged/migrated |
| Unfixed Critical vulnerability >90 days | Security responsibility |

### 5.2 Archival Process

1. Contact repository maintainer to confirm
2. If no response within 7 days, escalate to organization admin decision
3. Update README.md with archival notice:
   ```
   > ⚠️ This project is archived and no longer maintained. See [alternative].
   ```
4. Execute `gh repo archive huaweicloud/{repo}`
5. Record in the organization governance report

### 5.3 Deletion Conditions

Deletion may be considered if **all** of the following are met:

- Stars = 0 and Forks = 0
- No activity for over 730 days
- Maintainer confirms deletion
- Organization admin approves

> ⚠️ Back up before deletion; deletion is irreversible.

---

## 6. Roles & Responsibilities

### 6.1 Role Definitions

| Role | Permission | Responsibility |
|------|------|------|
| **Organization admin** | Org-level Owner | Set governance policy, approve archival/deletion, monthly audit |
| **Repository Owner** | Repo Admin | First responsible for repo compliance, branch protection config, security vulnerability response |
| **Maintainer** | Repo Write/Maintain | Daily maintenance, Issue/PR handling, code review |
| **Contributor** | Fork + PR | Submit code/documentation contributions |
| **Community user** | Read + Issue | Use the project, provide feedback |

### 6.2 Organization Admin Responsibilities (OSPO function)

1. Maintain templates and standards in the `.github` organization repository
2. Execute monthly governance audits and produce audit reports
3. Track and drive remediation of non-compliant repositories
4. Review and initialize new repositories
5. Coordinate organization-level security incidents

### 6.3 Repository Owner Commitment

Becoming a Repository Owner means committing to:

1. Ensure the repository meets L1 admission standards
2. Within 60 days of Stars ≥ 20, upgrade to L2 standards
3. Within 90 days of Stars ≥ 50, upgrade to L3 standards
4. Handle Issues and security vulnerabilities per SLA
5. Proactively initiate archival when maintenance stops

---

## 7. Compliance Checks & Metrics

### 7.1 Check Frequency

| Check Type | Frequency | Coverage | Execution |
|----------|----------|----------|----------|
| New repo check | Real-time (on creation) | New repositories | Creation script auto |
| Monthly audit | 1st of each month | All active repositories | governance-audit.yml |
| Quarterly deep audit | End of each quarter | L2 + L3 repositories | Manual + scripts |
| On-demand check | As needed | Specific repositories | `gh api` |

### 7.2 Core KPIs

| Metric | Current | L1 Target | L2 Target |
|------|:-----:|:------:|:------:|
| License coverage | 80.0% | **100%** | 100% |
| Branch protection rate (L2 repos) | ~7% | — | **100%** |
| Single-maintainer rate | 43.2% | — | ≤10% |
| Community files average | 0.98/6 | — | ≥3/6 |
| Security alerts (Critical) | 135 | — | ≤10 |
| Issue first response (median) | — | — | ≤7 days |

### 7.3 Violation Handling Process

```
Audit finds violation → auto-create Issue (priority/high) → @mention repo Owner
    ↓
No response in 7 days → escalate to organization admin
    ↓
No remediation in 30 days (blocking) → organization admin enforces
    ↓
No remediation in 60 days → initiate archival
```

### 7.4 Exemption Mechanism

Temporary exemptions may be requested in the following cases:

- Private repositories (Free plan doesn't support branch protection): auto-exempt L2-1
- Mirror repositories: auto-exempt Issue/PR related items
- Special scenarios with clear alternatives: submit exemption request, organization admin approves

Exemptions must be clearly marked in the repository README or .github/GOVERNANCE.md with the exempted items and reasons.

---

## 8. Appendix

### Appendix A: Checklists (quick reference)

#### New Repository Checklist

```
[ ] LICENSE file (Apache-2.0)
[ ] README.md (project intro + installation + usage example)
[ ] Repository description
[ ] Topics tags (≥3)
[ ] Issue label system (type/* + priority/* + status/* + area/* etc.)
[ ] Default branch = main
[ ] Issues enabled
[ ] .github/ISSUE_TEMPLATE/ (bug_report + feature_request + config)
[ ] .github/PULL_REQUEST_TEMPLATE.md
[ ] .github/dependabot.yml
```

#### Existing Repository Upgrade to L2 Checklist

```
[ ] Branch protection (require PR + 1 review)
[ ] Add ≥1 additional write-permission member
[ ] SECURITY.md
[ ] CONTRIBUTING.md
[ ] CODE_OF_CONDUCT.md
[ ] Enable Dependabot
[ ] PULL_REQUEST_TEMPLATE.md
```

### Appendix B: License Selection Guide

| Scenario | Recommended | Alternative |
|------|------|------|
| General SDK / library | Apache-2.0 | MIT |
| Strong copyleft | GPL-3.0 | — |
| Permissive | MIT | BSD-3-Clause |
| Mozilla projects | MPL-2.0 | — |
| Dataset | CC-BY-4.0 | CC0-1.0 |
| Documentation | CC-BY-4.0 | — |

### Appendix C: Related Resources

- GitHub community health docs: https://docs.github.com/en/communities
- OpenSSF Scorecard: https://securityscorecards.dev
- OSI-approved licenses: https://opensource.org/licenses
- Semantic Versioning: https://semver.org
- Conventional Commits: https://www.conventionalcommits.org
- Contributor Covenant: https://www.contributor-covenant.org

### Appendix D: Template File Index

All organization-level templates live in the `huaweicloud/.github` repository:

| File Path | Purpose |
|----------|------|
| `LICENSE` | Default license (Apache-2.0) |
| `CONTRIBUTING.md` | Organization-level contribution guide |
| `SECURITY.md` | Security vulnerability reporting policy |
| `CODE_OF_CONDUCT.md` | Contributor code of conduct |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Bug report form |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | Feature request form |
| `.github/ISSUE_TEMPLATE/config.yml` | Issue config |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR template |
| `.github/dependabot.yml` | Dependency update config |
| `.github/workflows/stale-manager.yml` | Stale Issue/PR auto-cleanup |
| `.github/workflows/governance-audit.yml` | Monthly governance audit |

---

> *This document was drafted by Hermes Agent and will take effect after TMG (Technical Management Group) review.*
> *After taking effect, all new repositories must meet L1 standards. Existing repositories must gradually comply per the tiered timeline in Section 8.*
