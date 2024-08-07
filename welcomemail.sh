#!/bin/bash

# 引数からユーザー情報を取得
EMAIL="$1"
FIRST_NAME="$2"
LAST_NAME="$3"
URL="$4"
CC_EMAIL="$5"

# 本文
NEW="/new.txt"
TRANS="/transfer.txt"
IFK="/IFK.txt"

# メールの件名と本文を作成
SUBJECT=""
BODY=""

# 送信日の翌土曜日の日付を計算
TODAY=$(date +%s)
NEXT_SATURDAY=$(date -d "next saturday" +%m/%d)

# テンポラリファイルの作成
TEMP_FILE=$(mktemp)

if [[ "$URL" == "IFK" ]]; then
    SUBJECT="Special Update for IFK Members"
    BODY="$IFK"
elif [[ "$BODY" == *"【未定】"* ]]; then
    SUBJECT="【NW/インフラ事業部】ようこそ！NW/インフラ事業部へ"
    BODY="$NEW"
else
    SUBJECT="【NW/インフラ事業部】ようこそ！NW/インフラ事業部へ"
    BODY="$TRANS"
fi

# ファイルの内容を処理
awk -v insert="$BODY" -v date="$NEXT_SATURDAY" '
  /【A】/ {
    sub(/\【A\】/, insert)
  }
  /【B】/ {
    sub(/\【B\】/, date)
  }
  {
    print
  }
' "$BODY" > "$TEMP_FILE"

# メール送信
{
    echo "To: $EMAIL"
    echo "Cc: $CC_EMAIL, div_nw-infra_leader@secure-i.jp"
    echo "Subject: $SUBJECT"
    echo
    echo -e "$TEMP_FILE"
} | sendmail -t

# メール送信結果を確認
if [ $? -eq 0 ]; then
    echo "Email sent successfully to $EMAIL with CC to $CC_EMAIL."
else
    echo "Failed to send email to $EMAIL."
    exit 1
fi
