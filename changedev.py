from flask import Flask, request
import requests
import re
import json
import subprocess

app = Flask(__name__)

# SlackのWebhook URL
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/your/slack/webhook'

@app.route('/backlog-webhook', methods=['POST'])
def backlog_webhook():
    data = request.get_json()

    # Backlogの通知データに「content」と「summary」が含まれているか確認
    if 'content' in data and 'summary' in data['content']:
        summary = data['content']['summary']

        # 「【事業部変更通知】」が含まれている場合のみ処理
        if '【事業部変更通知】' in summary:
            description = data['content'].get('description', '')
            user_info = extract_user_info(description)
            if user_info:
                if validate_user_info(user_info):
                    if create_wordpress_user(user_info):
                        task_id = data['content']['key_id']
                        send_welcome_email(user_info, description)
                        update_backlog_task(task_id)
                        return '', 200  # 正常終了
                    else:
                        send_slack_notification(f'Failed to create user. {user_info}')
                        return '', 500  # 異常終了
                else:
                    send_slack_notification(f'User registration failed due to invalid characters: {user_info}')
                    return '', 400  # 異常終了
    return '', 200

def extract_user_info(data):
    trigger_text = "下記ご確認下さい。"
    trigger_index = data.find(trigger_text)

    # トリガーテキストが見つからない場合はNoneを返す
    if trigger_index == -1:
        return None

    data_after_trigger = data[trigger_index + len(trigger_text):].strip()

    # ユーザ情報を抽出する正規表現パターン
    pattern = re.compile(r'\n(\w{3})([\u3000\u0020])([\w\s]+)さん\n([\w\.-]+@[\w\.-]+\.\w+)')
    match = pattern.search(data_after_trigger)

    if match:
        url = match.group(1).upper()
        full_name = match.group(3).strip().split()
        last_name = full_name[0] if len(full_name) > 0 else ""
        first_name = full_name[1] if len(full_name) > 1 else ""
        email = match.group(4)

        user_info = {
            'url': url,
            'last_name': last_name,
            'first_name': first_name,
            'email': email,
            'username': email
        }
        return user_info
    return None

def validate_user_info(user_info):
    # 特殊文字を検出する正規表現パターン
    special_characters_pattern = re.compile(r'[^\w\s@.-]')

    # 苗字と名前に特殊文字が含まれていないか確認
    if special_characters_pattern.search(user_info['last_name']) or special_characters_pattern.search(user_info['first_name']):
        return False
    return True

def create_wordpress_user(user_info):
    wp_api_url = 'https://your-wordpress-site.com/wp-json/wp/v2/users'
    wp_admin_user = 'admin_username'
    wp_admin_password = 'admin_password'

    response = requests.post(
        wp_api_url,
        auth=(wp_admin_user, wp_admin_password),
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'username': user_info['username'],
            'email': user_info['email'],
            'first_name': user_info['first_name'],
            'last_name': user_info['last_name'],
            'roles': ['author'],
            'nickname': f"{user_info['last_name']} {user_info['first_name']}",
            'name': f"{user_info['last_name']} {user_info['first_name']}",
            'notify': True
        })
    )

    if response.status_code == 201:
        print('User created successfully.')
        send_slack_notification(f'User created successfully: {user_info["email"]}')
        return True
    else:
        send_slack_notification(f'Failed to create user. Status code: {response.status_code}, Response: {response.text}')
        return False

def send_welcome_email(user_info, description):
                # メールの種類を決定
                if user_info['url'] == 'IFK':
                    email_type = 'C'
                elif '【未定】' in description:
                    email_type = 'A'
                else:
                    email_type = 'B'

    try:
        # welcomemail.shスクリプトを呼び出してメールを送信
        subprocess.run(['./welcomemail.sh', user_info['email'], user_info['first_name'], user_info['last_name'], email_type], check=True)
        print(f"Welcome email script executed for {user_info['email']}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute welcome email script: {str(e)}")
        send_slack_notification(f"Failed to execute welcome email script for {user_info['email']}. Error: {str(e)}")

def send_slack_notification(message):
    payload = {
        'text': message
    }
    # Slackに通知を送信
    requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'})

def update_backlog_task(task_id):
    try:
        # update_backlog_task.shスクリプトを呼び出してBacklogタスクを更新
        subprocess.run(['./update_backlog_task.sh', str(task_id)], check=True)
        print(f"Backlog task update script executed for task ID {task_id}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute Backlog task update script: {str(e)}")
        send_slack_notification(f"Failed to execute Backlog task update script for task ID {task_id}. Error: {str(e)}")

def test_extract_user_info():
    test_data = """
※本メールは事業部が変更された為、自動で送信されています。
各位

お疲れ様です
工藤です。

下記ご確認下さい。

SIR大和谷 卓やさん
t.yamatoya@secure-i.jp

【未定】から【NW・インフラ事業部】へ変更となりました。
【担当営業】：工藤 遼平

以上、宜しくお願い致します。
"""
    # テストデータからユーザ情報を抽出して検証
    user_info = extract_user_info(test_data)
    if user_info:
        if validate_user_info(user_info):
            print(f"Extracted user info from test data: {user_info}")
        else:
            print("User info contains invalid characters.")
    else:
        print("Failed to extract user info.")

if __name__ == '__main__':
    test_extract_user_info()
    app.run(host='0.0.0.0', port=5000)
