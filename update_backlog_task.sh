#!/bin/bash

TASK_ID=$1

# Backlog APIのURLとAPIキーを設定
BACKLOG_API_URL="https://your-backlog-space.backlog.com/api/v2/issues/$TASK_ID"
API_KEY="your_backlog_api_key"

# タスクを更新するためのデータをJSON形式で作成
UPDATE_DATA=$(cat <<EOF
{
    "statusId": 2,
    "comment": "完了：\nアカウント追加\nWelcomeメール送信\n\n未完了：\nML登録"
}
EOF
)

# Backlog APIを使用してタスクを更新
curl -X PATCH -H "Content-Type: application/json" -d "$UPDATE_DATA" "$BACKLOG_API_URL?apiKey=$API_KEY"

# スクリプトが失敗した場合、Slackに通知
if [ $? -ne 0 ]; then
    curl -X POST -H 'Content-type: application/json' --data "{\"text\":\"Failed to update Backlog task $TASK_ID\"}" https://hooks.slack.com/services/your/slack/webhook
    exit 1
fi

exit 0
