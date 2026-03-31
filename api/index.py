from flask import Flask, request, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
from time import time
from datetime import datetime
import os

app = Flask(__name__)

def convert_unix(unix):
    return datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S') if unix else None

def extract_region_via_script(username):
    try:
        headers = {
            "Host": "www.tiktok.com",
            "user-agent": "Mozilla/5.0 (Linux; Android 8.0.0; Plume L2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Mobile Safari/537.36",
        }
        response = requests.get(f'https://www.tiktok.com/@{username}', headers=headers, timeout=10)
        if response.status_code != 200:
            return "N/A"
        soup = BeautifulSoup(response.text, 'html.parser')
        user_data_script = None
        for script in soup.find_all('script'):
            if script.string and 'userInfo' in script.string:
                user_data_script = script.string
                break
        if not user_data_script:
            return "N/A"
        data = json.loads(user_data_script)
        user = data.get('__DEFAULT_SCOPE__', {}).get('webapp.user-detail', {}).get('userInfo', {}).get('user', {})
        return user.get('region', 'N/A')
    except:
        return "N/A"

def get_user_info(username):
    try:
        url = f'https://tiktok.com/@{username}'
        headers = {'user-agent': 'Mozilla/5.0'}
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", {"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"})
        data = json.loads(script.string)
        user = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]["user"]
        stats = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]["stats"]
        return {
            "nickname": user.get("nickname"),
            "username": user.get("uniqueId"),
            "profile_pic": user.get("avatarLarger"),
            "bio": user.get("signature") or "User has no about",
            "followers": stats.get("followerCount"),
            "following": stats.get("followingCount"),
            "likes": stats.get("heart"),
            "user_id": user.get("id"),
            "created": convert_unix(user.get("createTime")),
            "nickname_edited": convert_unix(user.get("nickNameModifyTime")),
            "username_changed": convert_unix(user.get("uniqueIdModifyTime")),
            "region": extract_region_via_script(username)
        }
    except:
        return None

def check_passkey(username):
    try:
        iid = int(bin(int(time()))[2:].zfill(32) + "0" * 32, 2)
        did = int(bin(int(time() + time() * 0.0004))[2:].zfill(32) + "0" * 32, 2)
        url = f'https://api16-normal-c-useast1a.tiktokv.com/passport/find_account/tiktok_username/?request_tag_from=h5&iid={iid}&device_id={did}&ac=wifi&channel=googleplay&aid=567753'
        payload = f'mix_mode=1&username={username}'
        r = requests.post(url, data=payload, timeout=10).json()
        token = r['data']['token']
        check_url = f'https://api16-normal-c-useast1a.tiktokv.com/passport/auth/available_ways/?request_tag_from=h5&not_login_ticket={token}&iid={iid}&device_id={did}&ac=wifi&channel=googleplay&aid=567753'
        result = requests.get(check_url, timeout=10).json()
        return result['data'].get('has_passkey', False)
    except:
        return False

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path == 'lookup':
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Username is required."}), 400
        user_info = get_user_info(username)
        if not user_info:
            return jsonify({"error": "User not found."}), 404
        user_info["has_passkey"] = check_passkey(username)
        return jsonify(user_info)
    return send_from_directory(os.path.dirname(__file__), 'index.html')

app = app
