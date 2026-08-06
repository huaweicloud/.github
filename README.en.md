# huaweicloud/.github

> **Language:** English | [中文](./README.md)

The governance configuration center for the HUAWEI CLOUD organization. This repository hosts organization-level governance infrastructure, reused by all repositories in the organization.

## Directory Structure

```
.github/
├── ISSUE_TEMPLATE/        # Issue templates (bug / feature)
├── PULL_REQUEST_TEMPLATE.md
├── workflows/             # Organization-level governance workflows
│   ├── issue-bot.yml      # Issue auto-classification & management
│   ├── triage-issue.yml   # Issue Triage
│   ├── sla-monitor.yml    # SLA monitoring
│   ├── stale-manager.yml  # Stale issue management
│   ├── weekly-report.yml  # Weekly report
│   ├── monthly-report.yml # Monthly report
│   ├── daily-reminder.yml # Daily reminder
│   ├── status-transition.yml # Issue/PR status transitions
│   └── sync-to-gitcode.yml   # GitCode sync
├── scripts/               # Governance scripts
├── configs/               # Rule configs (triage / SLA / stale / notification)
├── templates/             # Report templates
└── actions/               # Reusable Actions
```

## Core Capabilities

### 1. Issue Management
- **Auto-classification**: Automatically labels type/priority/area and assigns owners when an Issue is created
- **SLA monitoring**: Monitors response/resolution deadlines by priority, auto-escalates on timeout
- **Stale management**: Periodically cleans up long-inactive Issues
- **Reports**: Weekly / monthly / SLA daily reports auto-generated

### 2. Repository Creation
New repositories are requested via [repository-requests](https://github.com/huaweicloud/repository-requests); this repository provides governance configuration templates.

### 3. Notifications
- **Feishu**: Issue events, SLA alerts, report push
- **Email**: Report emails (SMTP)

## Usage

Issue management for all repositories in the organization inherits this repository's governance capabilities by default. Rule configs are in the `configs/` directory and can be adjusted as needed.

## Related Documents

- [Governance](GOVERNANCE.en.md)
- [Issue Automation Workflow](docs/issues自动化管理流程.en.md)
- [Repository Creation Process](docs/建仓流程文档.en.md)
- [PR Workflow & Standards](docs/PR流程与规范.en.md)
