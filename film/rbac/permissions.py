"""岗位 × 操作权限矩阵（M16.2-F02 / M16.3-F01：越权被拒并留痕）。"""
from . import roles

OPERATIONS = ("script_edit", "casting_edit", "board_edit", "generate",
              "edit", "mix", "grade", "export", "budget", "member_manage")

# 岗位 → 可执行操作集合（未知岗位/操作一律拒绝，fail-closed）
PERMISSION_MATRIX = {
    "showrunner": set(OPERATIONS),
    "director": {"casting_edit", "board_edit", "generate", "export"},
    "writer": {"script_edit"},
    "editor": {"edit", "export"},
    "sound": {"mix"},
    "colorist": {"grade"},
    "qc": {"export"},
    "legal": set(),
}


def can(position, operation):
    """岗位是否可执行某操作。未知岗位/操作 → False。"""
    if position not in roles.FILM_POSITIONS:
        return False
    if operation not in OPERATIONS:
        return False
    return operation in PERMISSION_MATRIX.get(position, set())
