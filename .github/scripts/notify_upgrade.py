#!/usr/bin/env python3
"""治理升级通知 - 支持飞书(可选) + 邮件 + GitHub Issue 三渠道

读取 governance_upgrade.py 的 upgrades.json，对每个升级仓库：
1. 飞书卡片（可选：配置了 FEISHU_* 才发送）
2. 邮件（可选：SMTP 配置了才发送，收件人来自 maintainer-rules.yml 或 EMAIL_REPORT_TO）
3. GitHub Issue（在升级仓库创建 Issue，@ 维护者，GitHub 自动通知）
"""

import os
import sys
import json
import yaml
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from email_notify import send_email

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_ADMIN_OPEN_ID = os.environ.get("FEISHU_ADMIN_OPEN_ID", "")
UPGRADES_FILE = os.environ.get("UPGRADES_FILE", "upgrades.json")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("BOT_TOKEN", ""))
GITHUB_API = "https://api.github.com"
GITHUB_ORG = os.environ.get("GITHUB_ORG", "huaweicloud")
MAINTAINER_RULES = os.environ.get("MAINTAINER_RULES", ".github/configs/maintainer-rules.yml")

# 飞书开关（默认可选，配了凭据才发）
FEISHU_ENABLED = os.environ.get("FEISHU_ENABLED", "1") == "1"
# 邮件开关
EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "1") == "1"
# GitHub Issue 开关
GITHUB_ISSUE_ENABLED = os.environ.get("GITHUB_ISSUE_ENABLED", "1") == "1"


def load_maintainer_map():
    """读取 maintainer-rules.yml，返回 {github用户名: email} 及默认管理员"""
    try:
        with open(MAINTAINER_RULES, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        maintainers = cfg.get("maintainers", {})
        user_email = {}
        for role, info in maintainers.items():
            github = info.get("github", "")
            email = info.get("email", "")
            if github and email:
                user_email[github] = email
        return user_email
    except Exception as e:
        print(f"Failed to load maintainer rules: {e}")
        return {}


def repo_maintainers(repo):
    """获取仓库的维护者（collaborators 中的 admin/maintain），返回 (github列表, email列表)"""
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    users = []
    try:
        r = requests.get(f"{GITHUB_API}/repos/{GITHUB_ORG}/{repo}/collaborators?per_page=100",
                         headers=headers, timeout=30)
        if r.status_code == 200:
            for c in r.json():
                perms = c.get("permissions", {})
                if perms.get("admin") or perms.get("maintain"):
                    users.append(c["login"])
    except Exception as e:
        print(f"Failed to get collaborators for {repo}: {e}")

    # 用维护者映射补充邮箱
    user_email = load_maintainer_map()
    emails = [user_email[u] for u in users if u in user_email]
    return users, emails


def get_tenant_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    resp = requests.post(url, json=data, timeout=15)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    print(f"Feishu auth failed: {result.get('msg')}")
    return None


def send_feishu(open_id, card):
    token = get_tenant_token()
    if not token:
        return False
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    body = {"receive_id": open_id, "msg_type": "interactive", "content": json.dumps(card, ensure_ascii=False)}
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=body, timeout=15)
    result = resp.json()
    if result.get("code") == 0:
        return True
    print(f"Feishu send failed: {result.get('msg')}")
    return False


def build_feishu_card(upgrade):
    repo = upgrade["repo"]
    stars = upgrade["stars"]
    tier = upgrade["tier"]
    files = upgrade.get("files", [])
    bp = upgrade.get("branch_protection", False)
    tier_name = {"L2": "L2 健康级", "L3": "L3 标杆级"}.get(tier, tier)

    elements = [
        {"tag": "markdown", "content": f"仓库 **{repo}** 的 Stars 已达 **{stars}**，自动升级至 **{tier_name}** 🎉"},
        {"tag": "hr"},
    ]
    if files:
        elements.append({"tag": "markdown", "content": f"**已自动补充以下配置：**\n" + "\n".join(f"• `{f}`" for f in files)})
    if bp:
        elements.append({"tag": "markdown", "content": "**已自动开启分支保护**（2 人 Approve + Code Owner Review + strict CI）"})
    if not files and not bp:
        elements.append({"tag": "markdown", "content": "该仓库已满足对应等级要求，无新增配置。"})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": f"huaweicloud 治理巡检 · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"🎉 {repo} 升级至 {tier_name}"}, "template": "green"},
        "elements": elements,
    }


def build_email_body(upgrade, maintainers, emails):
    repo = upgrade["repo"]
    stars = upgrade["stars"]
    tier = upgrade["tier"]
    files = upgrade.get("files", [])
    bp = upgrade.get("branch_protection", False)
    tier_name = {"L2": "L2 健康级", "L3": "L3 标杆级"}.get(tier, tier)

    lines = [
        f"# 🎉 恭喜 {repo} 升级至 {tier_name}",
        "",
        f"仓库 **{repo}** 的 Stars 已达 **{stars}**，已自动升级至 **{tier_name}**。",
        "",
    ]
    if files:
        lines.append("**已自动补充以下配置：**")
        lines += [f"- `{f}`" for f in files]
        lines.append("")
    if bp:
        lines.append("**已自动开启分支保护**（2 人 Approve + Code Owner Review + strict CI）")
        lines.append("")
    lines.append("---")
    lines.append(f"维护者：{'、'.join(f'@{u}' for u in maintainers) if maintainers else '（未配置）'}")
    lines.append(f"邮箱：{', '.join(emails) if emails else '（未配置）'}")
    lines.append("")
    lines.append("*本通知由 huaweicloud 治理巡检自动生成*")
    return "\n".join(lines)


def create_github_issue(repo, upgrade, maintainers):
    """在升级仓库创建 Issue，@ 维护者（GitHub 自带通知）"""
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    tier_name = {"L2": "L2 健康级", "L3": "L3 标杆级"}.get(upgrade["tier"], upgrade["tier"])
    files = upgrade.get("files", [])

    body = f"## 🎉 恭喜升级至 {tier_name}\n\n"
    body += f"仓库 Stars 已达 **{upgrade['stars']}**，已自动升级至 **{tier_name}**。\n\n"
    if files:
        body += "**已自动补充以下配置：**\n" + "\n".join(f"- `{f}`" for f in files) + "\n\n"
    if upgrade.get("branch_protection"):
        body += "- 已开启分支保护（2 人 Approve + Code Owner Review + strict CI）\n\n"
    if maintainers:
        body += "请维护者核对：" + " ".join(f"@{u}" for u in maintainers) + "\n"

    payload = {"title": f"🎉 仓库升级至 {tier_name}", "body": body}
    try:
        r = requests.post(f"{GITHUB_API}/repos/{GITHUB_ORG}/{repo}/issues", headers=headers, json=payload, timeout=30)
        if r.status_code == 201:
            print(f"[GitHub Issue] Created for {repo}: {r.json().get('html_url')}")
            return True
        print(f"[GitHub Issue] Failed for {repo}: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"[GitHub Issue] Error for {repo}: {e}")
    return False


def main():
    if not os.path.exists(UPGRADES_FILE):
        print("No upgrades file, nothing to notify")
        return

    with open(UPGRADES_FILE, "r", encoding="utf-8") as f:
        upgrades = json.load(f)

    if not upgrades:
        print("No upgrades this cycle")
        return

    for upgrade in upgrades:
        repo = upgrade["repo"]
        maintainers, emails = repo_maintainers(repo)

        # 1. 飞书（可选）
        if FEISHU_ENABLED and FEISHU_APP_ID and FEISHU_APP_SECRET:
            card = build_feishu_card(upgrade)
            if send_feishu(FEISHU_ADMIN_OPEN_ID, card):
                print(f"[Feishu] sent for {repo}")
            else:
                print(f"[Feishu] FAILED for {repo}")

        # 2. 邮件（可选）
        if EMAIL_ENABLED:
            subject = f"🎉 {repo} 升级至 {'L2 健康级' if upgrade['tier']=='L2' else 'L3 标杆级'}"
            body = build_email_body(upgrade, maintainers, emails)
            to_emails = emails if emails else None  # 无维护者邮箱时用 EMAIL_REPORT_TO
            if send_email(subject=subject, body=body, to_emails=to_emails, is_html=False):
                print(f"[Email] sent for {repo}")
            else:
                print(f"[Email] skipped/failed for {repo}")

        # 3. GitHub Issue（可选，@ 维护者）
        if GITHUB_ISSUE_ENABLED and GITHUB_TOKEN:
            create_github_issue(repo, upgrade, maintainers)


if __name__ == "__main__":
    main()
