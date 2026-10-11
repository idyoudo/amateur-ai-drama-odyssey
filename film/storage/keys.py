"""对象键规范（M15.1-F02：users/{uid}/dramas/{pid}/ep{n}/shot{m}/{stage}/v{k}.ext）。"""
import re

KEY_RE = re.compile(r'^users/[^/]+/dramas/[^/]+/ep\d+/shot\d+/[a-z0-9_]+/v\d+\.[a-z0-9]+$')


def make_object_key(uid, pid, episode, shot, stage, version, ext):
    return "users/%s/dramas/%s/ep%d/shot%d/%s/v%d.%s" % (uid, pid, episode, shot, stage, version, ext)


def validate_object_key(key):
    """不变量校验（fail-closed）。返回违规列表，空列表 = 合规。"""
    v = []
    if not key:
        v.append("对象键为空")
    elif key.startswith("/") or ".." in key or key.startswith("."):
        v.append("对象键必须是相对路径，禁止绝对路径/越界：%r" % (key,))
    elif not KEY_RE.match(key):
        v.append("对象键不合规（应为 users/{uid}/dramas/{pid}/ep{n}/shot{m}/{stage}/v{k}.ext）：%r" % (key,))
    return v
