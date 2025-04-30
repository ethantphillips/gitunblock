from flask import Flask, request, jsonify
import base64
import requests
import os

app = Flask(__name__)

# ===== CONFIG =====
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "ethantphillips/mclcheck"
FILE_PATH = ".mcbypass_licenses.ini"
BRANCH = "main"

@app.route("/")
def home():
    return "GitHub License API is running."

@app.route("/update-license", methods=["POST"])
def update_license():
    data = request.get_json()
    license_key = data.get("key")
    action = data.get("action")

    if not GITHUB_TOKEN:
        return jsonify({"error": "GitHub token not set on server"}), 500

    if not license_key or not action:
        return jsonify({"error": "Missing license key or action"}), 400

    # Fetch current license file from GitHub
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch license file", "details": response.json()}), 500

    content_json = response.json()
    sha = content_json["sha"]
    decoded = base64.b64decode(content_json["content"]).decode("utf-8")

    # Modify license line
    lines = decoded.strip().splitlines()
    new_lines = []
    updated = False

    for line in lines:
        if line.strip().lower() == "ready":
            new_lines.append(line)
            continue
        if "=" not in line:
            new_lines.append(line)
            continue
        key, rest = line.split("=", 1)
        if key.strip() == license_key:
            parts = [p.strip() for p in rest.split(",")]
            if len(parts) >= 5 and parts[4].lower() != "active":
                return jsonify({"error": "License is not active"}), 403
            if action == "increment":
                try:
                    parts[3] = str(int(parts[3]) + 1)
                    updated = True
                except ValueError:
                    return jsonify({"error": "Device count is invalid"}), 500
            new_lines.append(f"{key}={','.join(parts)}")
        else:
            new_lines.append(line)

    if not updated:
        return jsonify({"error": "License key not found or not changed"}), 404

    # Upload modified file back to GitHub
    updated_content = "\n".join(new_lines)
    encoded_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"Updated license: {license_key}",
        "content": encoded_content,
        "sha": sha,
        "branch": BRANCH
    }

    push_response = requests.put(url, headers=headers, json=payload)
    if push_response.status_code in [200, 201]:
        return jsonify({"status": "success"})
    else:
        return jsonify({"error": "Failed to update GitHub", "details": push_response.json()}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
