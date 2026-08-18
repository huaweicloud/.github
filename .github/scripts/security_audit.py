#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub 敏感信息定期自扫描（兜底）

对 org:huaweicloud 公开仓库做 code search：
  1. GitHub token 前缀（ghp_/gho_/ghs_/ghu_/github_pat_ 等）
  2. AK/SK/API Key 候选文件 → 内容正则校验赋值语句 → 排除占位符示例
命中（排除误报 allowlist 与已知存量 known_issues）后通过飞书 + 邮件告警。
"""
import os
import re
import sys
import json
import time
import base64
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
MAX_KEY_FILES = int(os.environ.get("MAX_KEY_FILES", "15"))     # 每类密钥查询最多扫描文件数
MAX_KEY_TOTAL = int(os.environ.get("MAX_KEY_TOTAL", "60"))     # 密钥类扫描文件总数上限
MAX_KEY_FINDINGS = int(os.environ.get("MAX_KEY_FINDINGS", "30"))  # 密钥类最多上报命中数

_file_cache = {}

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
    first = True
    while page <= max_pages:
        path = f"/search/code?q={urllib.parse.quote(q)}&per_page={per_page}&page={page}"
        data = gh_get(path, accept="application/vnd.github+json")
        if not isinstance(data, dict):
            if first:
                return None  # 首页即失败，明确标记（区别于"无命中"）
            break
        first = False
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
        "key_searches": cfg.get("key_searches", []),
        "key_patterns": cfg.get("key_patterns", []),
        "placeholder_keywords": cfg.get("placeholder_keywords", []),
        "allow_paths": cfg.get("allow_paths", []),
        "allow_repos": cfg.get("allow_repos", []),
        "known_issues": cfg.get("known_issues", []),
    }


def fetch_file_text(repo, path):
    """通过 contents API 获取文件文本（>1MB 的返回 blob sha，跳过）；带进程内缓存去重"""
    key = f"{repo}/{path}"
    if key in _file_cache:
        return _file_cache[key]
    data = gh_get(f"/repos/{repo}/contents/{urllib.parse.quote(path)}")
    text = ""
    if isinstance(data, dict) and data.get("content"):
        try:
            text = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            text = ""
    _file_cache[key] = text
    return text


def mask(value):
    if len(value) <= 8:
        return value[:2] + "****"
    return value[:4] + "****" + value[-2:]


def is_placeholder(rules, value):
    v = value.lower()
    for kw in rules["placeholder_keywords"]:
        if kw in v:
            return True
    if len(set(v)) <= 2:
        return True
    if not any(c.isalpha() for c in v):
        return True
    return False


def scan_key_patterns(rules, repo, path):
    """内容正则校验：返回命中的 (label, 脱敏值) 列表"""
    text = fetch_file_text(repo, path)
    if not text:
        return []
    hits = []
    for pat in rules["key_patterns"]:
        regex = pat.get("regex", "")
        if not regex:
            continue
        try:
            for m in re.finditer(regex, text, re.IGNORECASE):
                value = m.group("value") if "value" in m.groupdict() else m.group(0)
                if is_placeholder(rules, value):
                    continue
                hits.append((pat.get("label", "key"), mask(value)))
        except re.error as e:
            print(f"Bad regex {regex!r}: {e}", file=sys.stderr)
    return hits


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


def build_report(today, new_findings, known_hits, search_failures=0):
    lines = [
        f"# huaweicloud 敏感信息安全扫描（{today}）",
        "",
        f"扫描范围：`org:{ORG}` 公开仓库代码",
        "检测模式：GitHub token 前缀（ghp_/gho_/ghs_/ghu_/github_pat_）",
        "           + AK/SK/API Key 硬编码赋值（内容正则校验，已排除示例占位符）",
        "",
    ]
    if search_failures:
        lines.append(
            f"### ⚠️ 警告：{search_failures} 个搜索查询执行失败（限流/token 异常/网络错误），"
            "本次结果为不完整扫描，请检查后重跑"
        )
        lines.append("")
    if new_findings:
        lines.append(f"### 🚨 新增命中 {len(new_findings)} 项")
        lines.append("| 仓库 | 文件 | 匹配模式 |")
        lines.append("|------|------|----------|")
        seen = set()
        for repo, path, label in new_findings:
            key = (repo, path, label)
            if key in seen:
                continue
            seen.add(key)
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
    search_failures = 0

    # 1) 标识符/token 前缀扫描
    for q in rules.get("queries", []):
        query = q.get("query", "")
        if not query:
            continue
        label = q.get("label", query)
        hits = search_code(f"org:{ORG} {query}")
        if hits is None:
            search_failures += 1
            time.sleep(3)
            continue
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
        time.sleep(3)

    # 2) AK/SK/API key 候选扫描（搜索候选 + 内容正则校验）
    key_found = 0
    key_scanned_total = 0
    for q in rules.get("key_searches", []):
        query = q.get("query", "")
        if not query:
            continue
        hits = search_code(f"org:{ORG} {query}")
        if hits is None:
            search_failures += 1
            time.sleep(3)
            continue
        key_scanned_query = 0
        for item in hits:
            repo = item.get("repository", {}).get("full_name", "")
            path = item.get("path", "")
            if is_allowed(rules, repo, path) or known_match(rules, repo, path):
                continue
            key_scanned_query += 1
            key_scanned_total += 1
            for label, val in scan_key_patterns(rules, repo, path):
                new_findings.append((repo, path, f"{label} ({val})"))
                key_found += 1
                if key_found >= MAX_KEY_FINDINGS:
                    break
            if key_scanned_query >= MAX_KEY_FILES or key_scanned_total >= MAX_KEY_TOTAL:
                break
        if key_found >= MAX_KEY_FINDINGS or key_scanned_total >= MAX_KEY_TOTAL:
            break
        time.sleep(3)

    report = build_report(today, new_findings, known_hits, search_failures)
    print(report)

    if new_findings or search_failures or ALWAYS_NOTIFY:
        if search_failures:
            subject = f"⚠️ huaweicloud 敏感信息扫描不完整（{search_failures} 个查询失败）"
        elif new_findings:
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
