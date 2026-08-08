#!/usr/bin/env python3
"""治理月度巡检脚本 - 统计 GOVERNANCE §7.2 KPI 指标（优化版，控制 API 调用量）

指标:
1. License 覆盖率（全部活跃仓库）
2. 分支保护率（L2 仓库，Stars ≥ 20）
3. 单人维护率（全部活跃仓库，通过 members API 近似）
4. 社区文件均分（仅 L2/L3 仓库）
5. Security 告警（仅 L2/L3 仓库）
6. Issue 首次响应中位（仅 L2/L3 仓库）

输出 Markdown 报告 + 写文件。
"""

import os
import sys
import requests
from datetime import datetime, timezone
from statistics import median

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ORG = os.environ.get("GITHUB_ORG", "huaweicloud")
GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
OUTPUT_FILE = os.environ.get("AUDIT_OUTPUT", "output/audit_report.md")

SKIP_REPOS = {'.github', 'repository-requests', 'reports', 'community', 'repo-template',
              '_perm-test-sh', 'e2e-test-sdk', 'label-test-repo', 'test-create-repo-2',
              'test-en-repo', 'test-en-repo1', 'test-model-1', 'test-sdk-demo',
              'test-v5-final', 'final-e2e-test', 'compliance-pass-test', 'feishu-card-test',
              'pr-standards-test'}

COMMUNITY_FILES = ["LICENSE", "README.md", "CONTRIBUTING.md", "SECURITY.md",
                   "CODE_OF_CONDUCT.md", ".github/PULL_REQUEST_TEMPLATE.md"]


def get_repos():
    repos = []
    page = 1
    while True:
        url = f"{GITHUB_API}/orgs/{ORG}/repos?per_page=100&page={page}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return [r for r in repos if not r.get("archived") and not r.get("disabled")
            and r["name"] not in SKIP_REPOS]


def count_community_files(repo, branch):
    count = 0
    for path in COMMUNITY_FILES:
        url = f"{GITHUB_API}/repos/{ORG}/{repo}/contents/{path}?ref={branch}"
        if requests.get(url, headers=HEADERS, timeout=15).status_code == 200:
            count += 1
    return count


def has_branch_protection(repo, branch):
    url = f"{GITHUB_API}/repos/{ORG}/{repo}/branches/{branch}/protection"
    return requests.get(url, headers=HEADERS, timeout=15).status_code == 200


def median_first_response(repo):
    """开放 Issue 首次响应中位（小时）"""
    times = []
    page = 1
    while page <= 3:  # 限制扫描
        url = f"{GITHUB_API}/repos/{ORG}/{repo}/issues?state=open&per_page=30&page={page}&sort=created&direction=asc"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            break
        issues = [i for i in resp.json() if "pull_request" not in i]
        if not issues:
            break
        for issue in issues:
            created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
            c_url = f"{GITHUB_API}/repos/{ORG}/{repo}/issues/{issue['number']}/comments?per_page=1&sort=created&direction=asc"
            cr = requests.get(c_url, headers=HEADERS, timeout=15)
            if cr.status_code == 200 and cr.json():
                fc = datetime.fromisoformat(cr.json()[0]["created_at"].replace("Z", "+00:00"))
                times.append((fc - created).total_seconds() / 3600)
        page += 1
    return median(times) if times else None


def main():
    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN required")
        sys.exit(1)

    repos = get_repos()
    total = len(repos)
    print(f"Auditing {total} active repos")

    # 1. License 覆盖率（全部）
    license_count = sum(1 for r in repos if r.get("license"))

    # 划分 L2/L3
    high_repos = [r for r in repos if r.get("stargazers_count", 0) >= 20]
    l2_count = len(high_repos)

    # 2. 分支保护率（L2）
    protected_l2 = 0
    for r in high_repos:
        if has_branch_protection(r["name"], r.get("default_branch", "main")):
            protected_l2 += 1

    # 3. 单人维护率（通过 org 成员近似：写权限成员数由仓库 teams 决定，简化用 collaborators）
    #    这里用 L2/L3 抽查代替全量（避免 API 爆炸）
    single_maintainer = 0
    for r in high_repos[:15]:  # 抽查前 15 个 L2/L3
        url = f"{GITHUB_API}/repos/{ORG}/{r['name']}/collaborators?per_page=100"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            writers = [c for c in resp.json() if c.get("permissions", {}).get("push")
                       or c.get("permissions", {}).get("admin")
                       or c.get("permissions", {}).get("maintain")]
            if len(writers) <= 1:
                single_maintainer += 1

    # 4. 社区文件均分（L2/L3）
    scores = [count_community_files(r["name"], r.get("default_branch", "main")) for r in high_repos]
    community_avg = sum(scores) / len(scores) if scores else 0

    # 5. Security 告警（L2/L3，近似：统计启用 Dependabot 告警的仓库数）
    alerts_enabled = 0
    for r in high_repos:
        url = f"{GITHUB_API}/repos/{ORG}/{r['name']}/vulnerability-alerts"
        if requests.get(url, headers=HEADERS, timeout=15).status_code == 204:
            alerts_enabled += 1

    # 6. Issue 首次响应中位（L2/L3，抽样前 10）
    resp_times = []
    for r in high_repos[:10]:
        med = median_first_response(r["name"])
        if med is not None:
            resp_times.append(med)
    issue_median = median(resp_times) if resp_times else None

    # 计算
    license_rate = license_count / total * 100 if total else 0
    protected_rate = protected_l2 / l2_count * 100 if l2_count else 0
    single_rate = single_maintainer / 15 * 100 if high_repos else 0

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = f"""# huaweicloud 组织治理月度巡检报告

> 日期: {now}
> 组织: {ORG}
> 活跃仓库: {total}

## 核心指标 (KPI)

| 指标 | 当前值 | L1 目标 | L2 目标 | 状态 |
|------|:-----:|:------:|:------:|:----:|
| License 覆盖率 | {license_rate:.1f}% | **100%** | 100% | {'✅' if license_rate >= 100 else '❌'} |
| 分支保护率（L2仓库） | {protected_rate:.1f}% ({protected_l2}/{l2_count}) | — | **100%** | {'✅' if protected_rate >= 100 else '❌'} |
| 单人维护率 | {single_rate:.1f}% (抽查15个L2/L3) | — | ≤10% | {'✅' if single_rate <= 10 else '❌'} |
| 社区文件均分 | {community_avg:.1f}/6 | — | ≥3/6 | {'✅' if community_avg >= 3 else '❌'} |
| Security 告警(Dependabot) | {alerts_enabled}/{l2_count} 启用 | — | 100% | {'✅' if alerts_enabled == l2_count else '❌'} |
| Issue 首次响应（中位） | {('%.1fh' % issue_median) if issue_median else '—'} | — | ≤168h | {'✅' if issue_median and issue_median <= 168 else '❌'} |

## L2/L3 仓库（Stars ≥ 20）

| 仓库 | Stars | 分支保护 | 社区文件 |
|------|:-----:|:-------:|:-------:|
"""
    for i, r in enumerate(high_repos):
        stars = r.get("stargazers_count", 0)
        branch = r.get("default_branch", "main")
        prot = "✅" if has_branch_protection(r["name"], branch) else "❌"
        cf = scores[i] if i < len(scores) else 0
        report += f"| {r['name']} | {stars} | {prot} | {cf}/6 |\n"

    report += f"\n---\n*下次巡检: 下月 1 日 | 自动生成 by Hermes Agent*\n"

    print(report)
    os.makedirs(os.path.dirname(OUTPUT_FILE) or ".", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
