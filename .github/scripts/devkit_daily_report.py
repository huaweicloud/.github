#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""huaweicloud-devkit 每日运营日报（飞书）

指标：npm 下载量（当日/近7日）、GitHub stars（当前/近7日新增）、
      Issue 处理（今日新增/今日闭环）。
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

REPO = os.environ.get("REPO", "huaweicloud/huaweicloud-devkit")
NPM_PKG = os.environ.get("NPM_PACKAGE", "huaweicloud-devkit")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feishu_notify import send_notification


def gh_get(path, accept=None):
    headers = {"Accept": accept or "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(GITHUB_API + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"GH API {path}: {e.code}", file=sys.stderr)
        return None


def get_npm_downloads():
    """npm 下载量：当日 + 近7天（用显式日期范围，避开 last-7-days 端点 bug）"""
    today = datetime.now(timezone.utc)
    def _range(start, end):
        url = f"https://api.npmjs.org/downloads/point/{start}:{end}/{NPM_PKG}"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read()).get("downloads", 0)
        except Exception:
            return 0
    today_str = today.strftime("%Y-%m-%d")
    last7_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    today_dl = _range(today_str, today_str)
    week_dl = _range(last7_start, today_str)
    return today_dl, week_dl


def get_stars():
    """GitHub stars：当前总数 + 近7日新增（用 starred_at 时间戳）"""
    repo = gh_get(f"/repos/{REPO}")
    if not repo:
        return 0, 0
    total = repo.get("stargazers_count", 0)
    since = datetime.now(timezone.utc) - timedelta(days=7)
    stars7 = 0
    page = 1
    while page <= 10:
        data = gh_get(f"/repos/{REPO}/stargazers?per_page=100&page={page}",
                      accept="application/vnd.github.star+json")
        if not isinstance(data, list) or not data:
            break
        for item in data:
            starred = item.get("starred_at", "")
            if starred:
                try:
                    t = datetime.fromisoformat(starred.replace("Z", "+00:00"))
                    if t >= since:
                        stars7 += 1
                except ValueError:
                    pass
        if len(data) < 100:
            break
        page += 1
    return total, stars7


def get_forks():
    """Forks：当前总数 + 近7日新增（用 /forks 的 created_at）"""
    repo = gh_get(f"/repos/{REPO}")
    if not repo:
        return 0, 0
    total = repo.get("forks_count", 0)
    since = datetime.now(timezone.utc) - timedelta(days=7)
    forks7 = 0
    page = 1
    while page <= 10:
        data = gh_get(f"/repos/{REPO}/forks?per_page=100&page={page}&sort=newest")
        if not isinstance(data, list) or not data:
            break
        for item in data:
            created = item.get("created_at", "")
            if created:
                try:
                    t = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if t >= since:
                        forks7 += 1
                except ValueError:
                    pass
        if len(data) < 100:
            break
        page += 1
    return total, forks7


def get_watchers():
    """Watchers：关注/订阅数"""
    repo = gh_get(f"/repos/{REPO}")
    if not repo:
        return 0
    return repo.get("subscribers_count", 0)


def get_open_prs():
    """打开 PR 数（分页拉全）"""
    total = 0
    page = 1
    while page <= 10:
        data = gh_get(f"/repos/{REPO}/pulls?state=open&per_page=100&page={page}")
        if not isinstance(data, list) or not data:
            break
        total += len(data)
        if len(data) < 100:
            break
        page += 1
    return total


def get_open_issues():
    """打开 Issue 数（排除 PR，分页拉全）"""
    total = 0
    page = 1
    while page <= 10:
        data = gh_get(f"/repos/{REPO}/issues?state=open&per_page=100&page={page}")
        if not isinstance(data, list) or not data:
            break
        total += len([i for i in data if "pull_request" not in i])
        if len(data) < 100:
            break
        page += 1
    return total


def get_issues_week():
    """Issue 近7日新增、近7日闭环"""
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    opened = 0
    closed = 0
    data = gh_get(f"/search/issues?q=repo:{REPO}+is:issue+created:>{since}&per_page=1")
    if data and isinstance(data, dict):
        opened = data.get("total_count", 0)
    data2 = gh_get(f"/search/issues?q=repo:{REPO}+is:issue+closed:>{since}&per_page=1")
    if data2 and isinstance(data2, dict):
        closed = data2.get("total_count", 0)
    return opened, closed


def get_issues_today():
    """Issue：今日新增、今日闭环"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    opened_today = 0
    closed_today = 0
    for state in ("open", "closed", "all"):
        pass
    # 新增：今日创建
    data = gh_get(f"/search/issues?q=repo:{REPO}+is:issue+created:{today}&per_page=100")
    if data and isinstance(data, dict):
        opened_today = data.get("total_count", 0)
    # 闭环：今日关闭
    data2 = gh_get(f"/search/issues?q=repo:{REPO}+is:issue+closed:{today}&per_page=100")
    if data2 and isinstance(data2, dict):
        closed_today = data2.get("total_count", 0)
    return opened_today, closed_today


def build_report():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_dl, week_dl = get_npm_downloads()
    stars, stars7 = get_stars()
    forks, forks7 = get_forks()
    watchers = get_watchers()
    open_prs = get_open_prs()
    open_issues = get_open_issues()
    opened, closed = get_issues_today()
    opened_w, closed_w = get_issues_week()

    lines = [
        f"# huaweicloud-devkit 运营日报（{today}）",
        "",
        "### 下载量（npm）",
        f"- 今日下载：**{today_dl}**",
        f"- 近 7 日下载：**{week_dl}**",
        "",
        "### 社区活跃（GitHub）",
        f"- 当前 stars：**{stars}**（近7日 +{stars7}）",
        f"- 当前 forks：**{forks}**（近7日 +{forks7}）",
        f"- Watchers：**{watchers}**",
        "",
        "### 待处理事项",
        f"- 打开 PR：**{open_prs}**",
        f"- 打开 Issue：**{open_issues}**",
        "",
        "### Issue 处理",
        f"- 今日新增：**{opened}** / 今日闭环：**{closed}**",
        f"- 近 7 日新增：**{opened_w}** / 近 7 日闭环：**{closed_w}**",
        "",
    ]
    return "\n".join(lines), today_dl, week_dl, stars, stars7, forks, forks7, watchers, open_prs, open_issues, opened, closed


def main():
    report, *_ = build_report()
    subject = f"📊 huaweicloud-devkit 运营日报"
    ok = send_notification(subject, report, event_type="report.daily")
    print("Feishu report sent:", ok)
    print(report)


if __name__ == "__main__":
    main()
