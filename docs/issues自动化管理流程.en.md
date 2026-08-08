# huaweicloud Issue Automation Workflow

> **Language:** English | [中文](./issues自动化管理流程.md)

## Full Workflow

```
Issue created (GitHub / GitCode)
    ↓
┌──────────────────── GitHub ────────────────────┐  ┌────────────── GitCode ──────────────┐
│                                                 │  │                                     │
│ Issue Bot → auto-label + assign owner           │  │ gitcode_triage → API label + comment │
│     ↓                                           │  │     ↓                               │
│ SLA monitoring (hourly)                         │  │ SLA monitoring (hourly)              │
│     ↓                                           │  │     ↓                               │
│ Timeout → label + Feishu card + email           │  │ Timeout → Feishu card + email       │
│     ↓                                           │  │     ↓                               │
│ Status: pending → triaged → resolved            │  │ Stale: overdue → auto-close          │
│     ↓                                           │  │                                     │
│ Stale: overdue → auto-close                     │  │                                     │
│     ↓                                           │  │                                     │
│ Weekly/Monthly/SLA daily → Feishu + HTML email  │  │ merged into same report              │
└─────────────────────────────────────────────────┘  └─────────────────────────────────────┘
```

---

## 1. GitHub Issue Classification / Triage

### Trigger
- Issue Bot (`actions/issue-bot/`) runs automatically when an Issue is created (includes Feishu approval notification, slash commands)
- `triage-issue.yml` extends classification via the `issue-bot` Action

### Auto-label Rules

| Trigger | Label | Description |
|---------|------|------|
| Keyword in title/body | `type/bug` `type/feature` `type/documentation` `type/question` | keyword matching |
| Severity keywords | `priority/critical` `priority/high` `priority/medium` `priority/low` | auto-analysis |
| Area keywords | `area/api` `area/web` `area/ci-cd` etc. | per `triage-rules.yml` |

### Auto-assign Owner

| Label/Area | Owner |
|-----------|--------|
| `area/api` | @api-maintainer |
| `area/web` | @web-maintainer |
| `area/ci-cd` | @devops-maintainer |
| `area/sdk` | @sdk-maintainer |
| `area/security` | @security-maintainer |
| `area/performance` | @performance-maintainer |
| `area/database` | @database-maintainer |
| `type/bug` + `priority/critical` | @tech-lead |
| No match | @default-triage |

### Key Files

| File | Purpose |
|------|------|
| `actions/issue-bot/issue_bot.py` | Issue Bot core script |
| `configs/triage-rules.yml` | Classification rules (labels/owner mapping) |
| `workflows/triage-issue.yml` | Triage trigger |

---

## 2. GitHub Issue Lifecycle

### Status Transitions

```
status/pending          → Issue created, awaiting triage
status/triaged          → classified + assigned
status/in-progress      → in development (auto-marked by PR link)
status/resolved         → fixed (auto-marked on PR merge)
status/completed        → verified / admin closed
```

### Auto Status Changes

| Event | Status Change | Trigger |
|------|---------|------|
| Issue Bot classification done | `pending` → `triaged` | Issue Bot |
| PR linked with Fixes/Closes #N | `triaged` → `in-progress` | GitHub link |
| Linked PR merged | `in-progress` → `resolved` | workflow |
| Manual close | any → `completed` | admin |

### Stale Handling

| Type | Days to stale | Close buffer |
|------|---------|---------|
| `type/bug` | 60 days | 14 days |
| `type/feature` | 90 days | 14 days |
| `type/question` | 30 days | 7 days |
| `type/documentation` | 180 days | 14 days |
| `priority/critical` | 365 days | 30 days |

### Key Files

| File | Purpose |
|------|------|
| `workflows/stale-manager.yml` | Org-level stale management workflow |
| `configs/stale-rules.yml` | Days config |
| `workflows/status-transition.yml` | Status transition workflow |

---

## 3. Notification System (Feishu + Email)

### Dual-Channel Notifications

All events send both Feishu cards and HTML emails:

| Event | Feishu | Email |
|------|:---:|:---:|
| Issue created/closed | segmented card | HTML |
| SLA warning/breach/escalation | card + button | HTML |
| Issue about to stale | card | HTML |
| Weekly/Monthly/SLA daily report | segmented card + table | HTML table |

### Feishu Notifications

- Sent via Feishu Open API as DM card messages
- Reports: segmented structured cards, tables rendered with `lark_md`
- Alerts: color-coded (red=breach, orange=warning, blue=created, green=closed)
- Admin: Zhang Shuang

### Email Notifications

- Sent via SMTP (QQ `smtp.qq.com:587`)
- HTML format: blue gradient header, alternating row tables, red timeout highlights
- Recipient: 1993953167@qq.com
- Can be extended to per-maintainer email distribution

### Key Files

| File | Purpose |
|------|------|
| `workflows/feishu-notify.yml` | Reusable Feishu+email notify workflow |
| `scripts/feishu_notify.py` | Feishu card sender |
| `scripts/email_notify.py` | SMTP email sender (Markdown→HTML) |
| `configs/feishu-rules.yml` | Notification rules |

---

## 4. GitCode Issue Automation

### Notes
- GitCode Issues are **managed independently on the GitCode native platform**, not synced to GitHub
- Operated remotely via GitCode API v5 (labels, comments, status)
- API base: `https://api.gitcode.com/api/v5` (GitHub-style endpoints)
- Examples: `GET /orgs/huaweicloud/repos`, `GET /repos/{owner}/{repo}/issues`, `PATCH /repos/{owner}/{repo}/issues/{number}`
- All repos under `huaweicloud` are covered automatically

### Modules

| Module | Frequency | Function |
|------|------|------|
| **Triage** | every 6 hours | scan new Issues → keyword classify → API label + comment |
| **SLA monitoring** | hourly | timeout detection → Feishu + email alert |
| **SLA daily** | workdays 08:00 | timeout list → Feishu + email |
| **Stale management** | daily | stale Issues labeled → API close after 14 days |

### GitCode Triage Rules

Same as GitHub:
- `type/bug`: bug, 错误, crash, 崩溃, 报错
- `type/feature`: feature, 功能, 新增, enhancement
- `type/question`: question, 问题, 咨询
- `type/documentation`: doc, 文档, documentation
- Priority: critical(urgent/紧急) → high(important/重要) → low(minor/优化) → default medium

### GitCode Stale Rules

| Type | Days to stale | Close buffer |
|------|---------|---------|
| `type/bug` | 60 days | 14 days |
| `type/feature` | 90 days | 14 days |
| `type/question` | 30 days | 14 days |
| `type/documentation` | 180 days | 14 days |
| `priority/critical` | 365 days | 14 days |

### Key Files

| File | Purpose |
|------|------|
| `workflows/gitcode-triage.yml` | GitCode triage trigger |
| `workflows/gitcode-sla.yml` | GitCode SLA monitoring + daily |
| `workflows/gitcode-stale.yml` | GitCode stale management |
| `scripts/gitcode_triage.py` | GitCode classify/label script |
| `scripts/gitcode_sla.py` | GitCode SLA detection |
| `scripts/gitcode_stale.py` | GitCode stale close script |
| `scripts/gitcode_stats.py` | GitCode stats fetch (weekly) |

---

## 5. Issue Reports

### Report Types

| Report | Frequency | Scope | Content | Send |
|------|------|---------|------|------|
| **Weekly** | Mon 09:00 UTC | prev Mon~Sun (lookback) | created/closed/net change, SLA rate, type distribution, repo detail, GitCode stats | Feishu+email |
| **Monthly** | 1st of month | prev month (lookback) | monthly create/close rate, type share, top-10 repos, GitCode stats | Feishu+email |
| **SLA daily** | workdays 08:00 UTC | current | timeout Issue list, SLA rate | Feishu+email |

### Report Archive

All reports auto-archive to private repo `huaweicloud/reports`, by year/month:

```
reports/
└── 2026/
    ├── weekly/w31.md
    ├── monthly/2026-07.md
    └── sla/2026-08-03.md
```

### Metrics

| Dimension | GitHub | GitCode |
|------|:------:|:-------:|
| Issue total/open/closed | ✅ | ✅ |
| By type/priority | ✅ | ✅ |
| SLA rate | ✅ | ✅ |
| Repo ranking | ✅ | ✅ |
| Net change (created-closed) | ✅ | ✅ |

### Key Files

| File | Purpose |
|------|------|
| `workflows/issue-stats.yml` | stats+report trigger |
| `workflows/weekly-report.yml` | weekly trigger + archive |
| `workflows/monthly-report.yml` | monthly trigger + archive |
| `workflows/sla-daily.yml` | SLA daily trigger + archive |
| `scripts/github_stats.py` | GitHub issue stats |
| `scripts/gitcode_stats.py` | GitCode stats fetch |
| `scripts/stats_report.py` | merge + send + save |
| `scripts/archive_report.sh` | archive to reports repo |
| `templates/report-weekly.md` | weekly template |
| `templates/report-monthly.md` | monthly template |

---

## 6. SLA Standards

### GitHub

| Priority | First response | Resolution | Escalation |
|--------|------------|---------|---------|
| `priority/critical` | 4h | 1d | 8h |
| `priority/high` | 8h | 3d | 24h |
| `priority/medium` | 24h | 7d | 3d |
| `priority/low` | 48h | 30d | 14d |

### GitCode (same standards)

| Priority | First response | Resolution | Escalation |
|--------|------------|---------|---------|
| critical | 4h | 1d | 8h |
| high | 8h | 3d | 24h |
| medium | 24h | 7d | 3d |
| low | 48h | 30d | 14d |

### Key Files

| File | Purpose |
|------|------|
| `workflows/sla-monitor.yml` | GitHub SLA monitoring (hourly) |
| `workflows/gitcode-sla.yml` | GitCode SLA monitoring (hourly) |
| `scripts/sla_monitor.py` | GitHub SLA detection+alert |
| `scripts/gitcode_sla.py` | GitCode SLA detection+alert |
| `configs/sla-rules.yml` | SLA limits config |

---

## 7. Workflow Trigger Overview

| Workflow | Trigger | Frequency |
|----------|---------|------|
| `triage-issue.yml` | Issue opened | real-time |
| `issue-bot.yml` | Issue opened/edited + issue_comment | real-time |
| `issue-digest.yml` | schedule / workflow_dispatch | daily |
| `triage-agent.yml` | Issue opened/edited + issue_comment | real-time |
| `historical-triage.yml` | schedule / workflow_dispatch | on demand |
| `feishu-notify.yml` | workflow_call / workflow_dispatch | on demand |
| `sla-monitor.yml` | schedule | hourly |
| `stale-manager.yml` | schedule | Mon 02:30 UTC |
| `daily-reminder.yml` | schedule | workdays 01:00 UTC |
| `status-transition.yml` | PR opened/closed + issue closed | real-time |
| `issue-stats.yml` | schedule / workflow_dispatch | Mon 09:00 UTC |
| `weekly-report.yml` | schedule / workflow_dispatch | Mon 09:00 UTC |
| `monthly-report.yml` | schedule / workflow_dispatch | 1st of month |
| `sla-daily.yml` | schedule | workdays 08:00 UTC |
| `sync-to-gitcode.yml` | push main | real-time |
| `governance-audit.yml` | schedule / workflow_dispatch | 1st of month |
| `gitcode-triage.yml` | schedule | every 6h |
| `gitcode-sla.yml` | schedule | hourly |
| `gitcode-stale.yml` | schedule | daily 03:00 UTC |

---

## 8. Organization Secrets

> **Level note**: org-level secrets are configured with `visibility=all`, but propagation to **new repos** and the **`.github` config repo** is unreliable. Therefore `.github` uses **repo-level** secrets (same values); new repos get repo-level `BOT_TOKEN` + `GITCODE_TOKEN` written by the creation process (`setup_repo_secrets`).

| Secret | Purpose | Level |
|--------|------|------|
| `FEISHU_APP_ID` | Feishu app ID | org + .github repo-level |
| `FEISHU_APP_SECRET` | Feishu app secret | org + .github repo-level |
| `FEISHU_ADMIN_OPEN_ID` | admin open_id | org + .github repo-level |
| `SMTP_HOST` | QQ SMTP server (smtp.qq.com) | org + .github repo-level |
| `SMTP_PORT` | SMTP port (587) | org + .github repo-level |
| `SMTP_USER` | SMTP account | org + .github repo-level |
| `SMTP_PASS` | SMTP auth code | org + .github repo-level |
| `EMAIL_REPORT_TO` | report recipient | org + .github repo-level |
| `GITCODE_TOKEN` | GitCode API token | org + .github repo-level |
| `GITCODE_USERNAME` | GitCode username | org + .github repo-level |
| `ARCHIVE_TOKEN` | report archive (push to reports) | org + .github repo-level |
| `BOT_TOKEN` | cross-repo ops (checkout .github / create / approve) | org + written to new repos |
| `GITHUB_TOKEN` | GitHub API | default |

---

## 9. Admin Quick Reference

```powershell
# === GitHub ===
# View timeout Issues
gh issue list -R huaweicloud/<repo> -l "sla/breach"

# View pending Issues
gh issue list -R huaweicloud/<repo> -l "status/pending"

# View escalation Issues
gh issue list -R huaweicloud/<repo> -l "escalation"

# Manually trigger stats report
gh workflow run issue-stats.yml -R huaweicloud/.github

# Manually trigger SLA check
gh workflow run sla-monitor.yml -R huaweicloud/.github

# Manually test Feishu notify
gh workflow run feishu-notify.yml -R huaweicloud/.github -f event=test -f subject="test" -f body="content"

# === GitCode ===
gh workflow run gitcode-triage.yml -R huaweicloud/.github
gh workflow run gitcode-sla.yml -R huaweicloud/.github
gh workflow run gitcode-stale.yml -R huaweicloud/.github
```

---

## 10. Label System

### Type Labels `type/*`

| Label | Purpose | GitCode |
|------|------|:-----------:|
| `type/bug` | Bug report | ✅ |
| `type/feature` | Feature request | ✅ |
| `type/documentation` | Documentation | ✅ |
| `type/question` | Question | ✅ |

### Priority Labels `priority/*`

| Label | Purpose | GitCode |
|------|------|:-----------:|
| `priority/critical` | Urgent | ✅ |
| `priority/high` | High | ✅ |
| `priority/medium` | Medium | ✅ |
| `priority/low` | Low | ✅ |

### Status Labels `status/*`

| Label | Purpose | GitCode |
|------|------|:-----------:|
| `status/pending` | Pending | - |
| `status/triaged` | Triaged | - |
| `status/in-progress` | In progress | - |
| `status/resolved` | Resolved | - |
| `status/completed` | Completed | - |
| `status/stale` | About to stale | ✅ |
| `status/blocked` | Blocked | - |

### Area Labels `area/*`

| Label | Purpose |
|------|------|
| `area/api` | API |
| `area/web` | Web / frontend |
| `area/ci-cd` | CI/CD |
| `area/sdk` | SDK |
| `area/security` | Security |
| `area/performance` | Performance |
| `area/database` | Database / storage |

### SLA / Automation Labels

| Label | Purpose |
|------|------|
| `sla/breach` | SLA breached |
| `sla/warning` | SLA about to breach |
| `escalation` | Escalated |
| `agent/triaged` | Bot triaged |

### Community Labels

| Label | Purpose |
|------|------|
| `good first issue` | Beginner friendly |
| `help wanted` | Seeking help |

---

## 11. Pending Improvements

- [ ] Per-maintainer email distribution (currently all to admin)
- [x] GitCode `GITCODE_TOKEN` permission confirmed (fixed: token valid, sync/ops normal)
- [x] GitHub Issue slash commands (/assign, /priority, /label, /unlabel, /retriage, /close, /reopen)
- [ ] Issue trend charts (MoM)
- [ ] Feishu bot interactive commands (/assign, /priority etc.)
