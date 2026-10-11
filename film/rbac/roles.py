"""角色与岗位（M16.1-F02 六类技术角色 + M16.2-F01 八类影视岗位）。"""

# 技术角色（权限载体）
TECH_ROLES = ("owner", "admin", "writer", "editor", "reviewer", "viewer")

# 影视岗位（showrunner、导演、编剧、剪辑、声音、调色、QC、法务）
FILM_POSITIONS = ("showrunner", "director", "writer", "editor", "sound", "colorist", "qc", "legal")

POSITION_LABELS = {
    "showrunner": "剧集统筹",
    "director": "导演",
    "writer": "编剧",
    "editor": "剪辑",
    "sound": "声音",
    "colorist": "调色",
    "qc": "QC",
    "legal": "法务",
}
