#!/usr/bin/env python3
"""治理升级脚本 - 按 Stars 检测仓库 L2/L3 缺口并自动补齐配置

L1 基线（建仓时已注入）：LICENSE/README/CODEOWNERS/描述/Topics/Issues/main/标签
L2 健康（Stars ≥ 20）：SECURITY.md、CODE_OF_CONDUCT.md、dependabot.yml、分支保护(public)
L3 标杆（Stars ≥ 50）：CodeQL、CI/CD

当仓库 Stars 达到阈值时，自动补齐缺失配置，并输出升级通知信息供飞书/邮件发送。
"""

import os
import json
import requests
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ORG = os.environ.get("GITHUB_ORG", "huaweicloud")
GITHUB_API = "https://api.github.com"
DRY_RUN = "--dry" in os.environ.get("GOVERNANCE_ARGS", "") or "--dry" in __import__("sys").argv
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# 模板目录（workflow 已 checkout .github 到 .github-repo/）
TEMPLATE_DIR = os.environ.get("TEMPLATE_DIR", ".github-repo")

# 忽略的仓库（bot/测试/配置）
SKIP_REPOS = {'.github', 'repository-requests', 'reports', 'community', 'repo-template',
              '_perm-test-sh', 'e2e-test-sdk', 'label-test-repo', 'test-create-repo-2'}


def api(method, path, data=None):
    url = f"{GITHUB_API}{path}"
    body = json.dumps(data).encode() if data else None
    resp = requests.request(method, url, headers=HEADERS, data=body, timeout=30)
    if resp.status_code in (200, 201, 204):
        return resp.json() if resp.status_code != 204 and resp.content else {}
    return {}


def get_repos():
    repos = []
    page = 1
    while True:
        url = f"{GITHUB_API}/orgs/{ORG}/repos?per_page=100&page={page}&sort=stars"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return [r for r in repos if not r.get("archived") and r["name"] not in SKIP_REPOS]


def file_exists(repo, path):
    r = api("GET", f"/repos/{ORG}/{repo}/contents/{path}")
    return bool(r)


def create_file(repo, path, content, message):
    import base64
    if DRY_RUN:
        return True  # dry-run 模拟成功
    data = {"message": message, "content": base64.b64encode(content.encode()).decode()}
    existing = api("GET", f"/repos/{ORG}/{repo}/contents/{path}")
    if existing and "sha" in existing:
        data["sha"] = existing["sha"]
    result = api("PUT", f"/repos/{ORG}/{repo}/contents/{path}", data)
    return bool(result and ("content" in result or "commit" in result))


def read_template(filename):
    """从 .github 仓库读取模板文件（去掉语言切换头行）"""
    for path in [os.path.join(TEMPLATE_DIR, filename),
                 os.path.join(TEMPLATE_DIR, ".github", filename)]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    # 兜底模板
    defaults = {
        "SECURITY.md": "# Security Policy\n\nReport vulnerabilities via security advisory.\n",
        "CODE_OF_CONDUCT.md": "# Code of Conduct\n\nBe respectful and inclusive.\n",
        "dependabot.yml": "version: 2\nupdates:\n  - package-ecosystem: github-actions\n    directory: /\n    schedule:\n      interval: weekly\n",
        "codeql.yml": "",
    }
    return defaults.get(filename, "")


# L2 文件模板（从 .github 仓库根文件）
L2_FILES = [
    ("SECURITY.md", "SECURITY.md", "Add security policy (L2 upgrade)"),
    ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.md", "Add code of conduct (L2 upgrade)"),
    (".github/dependabot.yml", "dependabot.yml", "Add dependabot config (L2 upgrade)"),
]

# L3 文件模板
CODEQL_WORKFLOW = """name: CodeQL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 3 * * 0'

permissions:
  contents: read
  security-events: write

jobs:
  codeql:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
      - uses: github/codeql-action/analyze@v3
    strategy:
      fail-fast: false
      matrix:
        language: [python, javascript]
"""


def apply_branch_protection(repo, private):
    if private:
        return False  # Free plan 无法保护 private
    # 检查是否已有保护
    br = api("GET", f"/repos/{ORG}/{repo}/branches/main")
    if not br:
        return False
    payload = {
        "required_status_checks": {"strict": True, "contexts": ["lint", "test", "build"]},
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "required_approving_review_count": 2,
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
        },
        "restrictions": None,
    }
    if DRY_RUN:
        return True
    result = api("PUT", f"/repos/{ORG}/{repo}/branches/main/protection", payload)
    return bool(result)


def main():
    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN required")
        return

    repos = get_repos()
    upgrades = []  # [{repo, stars, tier, files: [...], branch_protection}]

    for repo in repos:
        name = repo["name"]
        stars = repo.get("stargazers_count", 0)
        private = repo.get("private", False)
        default_branch = repo.get("default_branch", "main")

        tier = "L1"
        if stars >= 50:
            tier = "L3"
        elif stars >= 20:
            tier = "L2"

        if tier == "L1":
            continue

        added_files = []
        branch_protected = False

        # L2 文件补齐
        for dest, template_name, msg in L2_FILES:
            if not file_exists(name, dest):
                content = read_template(template_name)
                if content and create_file(name, dest, content, msg):
                    added_files.append(dest)
                    print(f"[L2] {name}: added {dest}")

        # L2 分支保护（public 仓库，检查是否已有保护，无则补）
        if not private:
            prot = api("GET", f"/repos/{ORG}/{name}/branches/{default_branch}/protection")
            if not prot:
                if apply_branch_protection(name, private):
                    branch_protected = True
                    print(f"[L2] {name}: branch protection applied")

        # L3 文件补齐
        if tier == "L3":
            if not file_exists(name, ".github/workflows/codeql.yml"):
                if create_file(name, ".github/workflows/codeql.yml", CODEQL_WORKFLOW, "Add CodeQL workflow (L3 upgrade)"):
                    added_files.append(".github/workflows/codeql.yml")
                    print(f"[L3] {name}: added codeql.yml")

        if added_files or branch_protected:
            upgrades.append({
                "repo": name,
                "stars": stars,
                "tier": tier,
                "files": added_files,
                "branch_protection": branch_protected,
            })

    # 输出升级汇总（供飞书/邮件）
    print(f"\n=== Upgrade summary: {len(upgrades)} repos ===")
    print(json.dumps(upgrades, ensure_ascii=False, indent=1))

    # 保存到文件供后续通知（相对脚本目录，确保 workflow 中可定位）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    upgrades_path = os.path.join(script_dir, "..", "..", "upgrades.json")
    os.makedirs(os.path.dirname(upgrades_path), exist_ok=True)
    with open(upgrades_path, "w", encoding="utf-8") as f:
        json.dump(upgrades, f, ensure_ascii=False, indent=1)
    print(f"Upgrades saved to {upgrades_path}")


if __name__ == "__main__":
    main()
