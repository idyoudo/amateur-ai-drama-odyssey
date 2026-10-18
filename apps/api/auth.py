"""HTTP 登录鉴权（用户名密码 + HMAC 签名令牌，24 小时有效）。"""
import base64
import hashlib
import hmac
import json
import secrets
import time

TOKEN_TTL = 86400  # 24 小时


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", str(password).encode(), salt.encode(), 120000)
    return "pbkdf2$%s$%s" % (salt, base64.b64encode(dk).decode())


def verify_password(password, stored):
    try:
        algo, salt, digest = str(stored).split("$", 2)
    except ValueError:
        return False
    if algo != "pbkdf2":
        return False
    dk = hashlib.pbkdf2_hmac("sha256", str(password).encode(), salt.encode(), 120000)
    return hmac.compare_digest(base64.b64encode(dk).decode(), digest)


def sign_token(username, secret):
    payload = {"sub": username, "exp": int(time.time()) + TOKEN_TTL}
    data = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    return data + "." + sig


def verify_token(token, secret):
    if not token:
        return None
    try:
        data, sig = token.split(".", 1)
    except ValueError:
        return None
    expected = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    pad = "=" * (-len(data) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(data + pad).decode())
    except Exception:
        return None
    if payload.get("exp", 0) < int(time.time()):
        return None
    return payload.get("sub")


def check_credentials(username, password, env_username, env_password):
    if not env_username or not env_password:
        return False
    return (hmac.compare_digest(str(username or ""), env_username)
            and hmac.compare_digest(str(password or ""), env_password))
