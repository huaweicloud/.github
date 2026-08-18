#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub 敏感信息定期自扫描（兜底）

对 org:huaweicloud 公开仓库做 code search，检测敏感标识符 / GitHub token 前缀。
命中（排除误报 allowlist 与已知存量 known_issues）后通过飞书 + 邮件告警。
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from fnmatch import fnmatch
from datetime import datetime, timezone

import yaml

ORG = os.environ.get("GITHUB_ORG", "huaweicloud")
TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("BOT_TOKEN", ""))
GITHUB_API = "https://api.github.com"
RULES_FILE = os.environ.get(
    "SECURITY_AUDIT_RULES", ".github/configs/security-audit-rules.yml"
)
ALWAYS_NOTIFY = os.environ.get("ALWAYS_NOTIFY", "0") == "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feishu_notify import send_notification
from email_notify import send_email


def gh_get(path, accept=None, retries=2):
    headers = {"Accept": accept or "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    for attempt in range(retries):
        req = urllib.request.Request(GITHUB_API + path, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 403 and attempt < retries - 1:
                print(f"GH API {path}: 403 (rate limit), waiting...", file=sys.stderr)
                time.sleep(65)
                continue
            print(f"GH API {path}: {e.code}", file=sys.stderr)
            return None
        except Exception as ex:
            print(f"GH API {path}: {ex}", file=sys.stderr)
            return None
    return None


def search_code(q, per_page=100, max_pages=10):
    items = []
    page = 1
    while page <= max_pages:
        path = f"/search/code?q={urllib.parse.quote(q)}&per_page={per_page}&page={page}"
        data = gh_get(path, accept="application/vnd.github+json")
        if not isinstance(data, dict):
            break
        batch = data.get("items", [])
        items.extend(batch)
        total = data.get("total_count", 0)
        if not batch or len(items) >= total or len(batch) < per_page:
            break
        page += 1
        time.sleep(2)
    return items


def load_rules():
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Failed to load rules {RULES_FILE}: {e}", file=sys.stderr)
        cfg = {}
    return {
        "queries": cfg.get("queries", []),
        "allow_paths": cfg.get("allow_paths", []),
        "allow_repos": cfg.get("allow_repos", []),
        "known_issues": cfg.get("known_issues", []),
    }


def is_allowed(rules, repo, path):
    full = f"{repo}/{path}"
    for r in rules["allow_repos"]:
        if full.startswith(r):
            return True
    for p in rules["allow_paths"]:
        if fnmatch(path, p) or fnmatch(full, p):
            return True
    return False


def known_match(rules, repo, path):
    for k in rules["known_issues"]:
        if k.get("repo") == repo:
            for p in k.get("paths", []):
                if path == p or fnmatch(path, p):
                    return k
    return None


def build_report(today, new_findings, known_hits):
    lines = [
        f"# huaweicloud 敏感信息安全扫描（{today}）",
        "",
        f"扫描范围：`org:{ORG}` 公开仓库代码",
        "检测模式：邮箱标识符 + GitHub token 前缀（ghp_/gho_/ghs_/ghu_/github_pat_）",
        "",
    ]
    if new_findings:
        lines.append(f"### 🚨 新增命中 {len(new_findings)} 项")
        lines.append("| 仓库 | 文件 | 匹配模式 |")
        lines.append("|------|------|----------|")
        for repo, path, label in new_findings:
            lines.append(f"| `{repo}` | `{path}` | {label} |")
    else:
        lines.append("### ✅ 未发现新增敏感信息")
    lines.append("")

    seen = set()
    deduped_known = []
    for repo, path, note in known_hits:
        key = (repo, path)
        if key in seen:
            continue
        seen.add(key)
        deduped_known.append((repo, path, note))
    if deduped_known:
        lines.append(f"### 已知存量 {len(deduped_known)} 项（待修复）")
        lines.append("| 仓库 | 文件 | 说明 |")
        lines.append("|------|------|------|")
        for repo, path, note in deduped_known:
            lines.append(f"| `{repo}` | `{path}` | {note} |")
        lines.append("")

    lines.append("---")
    lines.append("*由 huaweicloud/.github 安全自扫描自动生成*")
    return "\n".join(lines)


def main():
    rules = load_rules()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_findings = []
    known_hits = []

    for q in rules.get("queries", []):
        query = q.get("query", "")
        if not query:
            continue
        label = q.get("label", query)
        hits = search_code(f"org:{ORG} {query}")
        for item in hits:
            repo = item.get("repository", {}).get("full_name", "")
            path = item.get("path", "")
            if is_allowed(rules, repo, path):
                continue
            kn = known_match(rules, repo, path)
            if kn:
                known_hits.append((repo, path, kn.get("note", "已知存量")))
            else:
                new_findings.append((repo, path, label))
        time.sleep(6)

    report = build_report(today, new_findings, known_hits)
    print(report)

    if new_findings or ALWAYS_NOTIFY:
        if new_findings:
            subject = f"🚨 huaweicloud 敏感信息扫描：新增 {len(new_findings)} 项"
        else:
            subject = f"✅ huaweicloud 敏感信息扫描（{today}）"
        ok = send_notification(subject, report, event_type="report.security")
        print("Feishu sent:", ok)
        send_email(subject=subject, body=report)
    else:
        print("No new findings, skip notification")


if __name__ == "__main__":
    main()
