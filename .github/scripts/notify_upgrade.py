#!/usr/bin/env python3
"""飞书通知仓库升级 - 读取 governance_upgrade.py 的 upgrades.json，发送恭喜 + 补的文件清单"""

import os
import json
import requests
from datetime import datetime, timezone

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_ADMIN_OPEN_ID = os.environ.get("FEISHU_ADMIN_OPEN_ID", "")
UPGRADES_FILE = os.environ.get("UPGRADES_FILE", "upgrades.json")


def get_tenant_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    resp = requests.post(url, json=data, timeout=15)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    print(f"Feishu auth failed: {result.get('msg')}")
    return None


def send_dm(open_id, card):
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


def build_card(upgrade):
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
        file_lines = "\n".join(f"• `{f}`" for f in files)
        elements.append({
            "tag": "markdown",
            "content": f"**已自动补充以下配置：**\n{file_lines}"
        })
    if bp:
        elements.append({
            "tag": "markdown",
            "content": "**已自动开启分支保护**（2 人 Approve + Code Owner Review + strict CI）"
        })
    if not files and not bp:
        elements.append({"tag": "markdown", "content": "该仓库已满足对应等级要求，无新增配置。"})

    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": f"huaweicloud 治理巡检 · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": f"🎉 {repo} 升级至 {tier_name}"}, "template": "green"},
        "elements": elements,
    }


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
        card = build_card(upgrade)
        if send_dm(FEISHU_ADMIN_OPEN_ID, card):
            print(f"Upgrade notification sent for {upgrade['repo']}")
        else:
            print(f"Upgrade notification FAILED for {upgrade['repo']}")


if __name__ == "__main__":
    main()
