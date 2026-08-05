import os
import time

from pymongo import MongoClient

from inginious.common.base import load_json_or_yaml
from inginious.frontend.user_manager import UserManager

config = load_json_or_yaml(os.environ.get("INGINIOUS_WEBAPP_CONFIG", "/inginious/configuration.yaml"))
username = os.environ.get("ADMIN_USER", "superadmin")
password = os.environ.get("ADMIN_PASSWORD", "superadmin")

client = MongoClient(config["mongo_opt"]["host"], serverSelectionTimeoutMS=5000)
for attempt in range(12):
    try:
        client.server_info()
        break
    except Exception as exc:
        print("waiting for mongodb: %s" % exc)
        time.sleep(5)

users = client[config["mongo_opt"]["database"]].users
result = users.update_one(
    {"username": username},
    {"$setOnInsert": {
        "username": username,
        "realname": username,
        "email": "%s@example.invalid" % username,
        "password": UserManager.hash_password(password),
        "bindings": {},
        "language": "en",
        "code_indentation": "4",
    }},
    upsert=True,
)
print("created user %s" % username if result.upserted_id else "user %s already present" % username)
