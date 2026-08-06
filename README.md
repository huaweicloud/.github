# huaweicloud/.github

> **语言切换：** [English](./README.en.md) | 中文

HUAWEI CLOUD 组织治理配置中心。本仓库承载组织级治理基础设施，供组织内所有仓库复用。

## 目录结构

```
.github/
├── ISSUE_TEMPLATE/        # Issue 模板（bug / feature）
├── PULL_REQUEST_TEMPLATE.md
├── workflows/             # 组织级治理工作流
│   ├── issue-bot.yml      # Issue 自动分类与管理
│   ├── triage-issue.yml   # Issue Triage
│   ├── sla-monitor.yml    # SLA 监控
│   ├── stale-manager.yml  # 过期 Issue 管理
│   ├── weekly-report.yml  # 周报
│   ├── monthly-report.yml # 月报
│   ├── daily-reminder.yml # 每日提醒
│   ├── status-transition.yml # Issue/PR 状态流转
│   └── sync-to-gitcode.yml   # GitCode 同步
├── scripts/               # 治理脚本
├── configs/               # 规则配置（triage / SLA / stale / 通知）
├── templates/             # 报告模板
└── actions/               # 可复用 Actions
```

## 核心能力

### 1. Issue 管理
- **自动分类**：Issue 提交后自动打类型/优先级/领域标签并分配负责人
- **SLA 监控**：按优先级监控响应与解决时限，超时自动升级
- **Stale 管理**：定期清理长期无活动的 Issue
- **报告**：周报 / 月报 / SLA 日报自动生成

### 2. 建仓流程
组织内新仓库通过 [repository-requests](https://github.com/huaweicloud/repository-requests) 申请，本仓库提供治理配置模板。

### 3. 通知
- **飞书**：Issue 事件、SLA 告警、报告推送
- **邮件**：报告邮件（SMTP）

## 使用方式

组织内各仓库的 Issue 管理默认继承本仓库的治理能力。各规则配置见 `configs/` 目录，可按需调整。

## 相关文档

- [治理规范](GOVERNANCE.md)
- [Issue 自动化管理流程](docs/issues自动化管理流程.md)
- [建仓流程文档](docs/建仓流程文档.md)
- [PR 流程与规范](docs/PR流程与规范.md)
