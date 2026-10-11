"""调色一致性（M11.2-F02：镜头间 ΔE ≤3、肤色区域 ≤2）。"""
from . import enums


def validate_color_delta(shot_de, skin_de):
    v = []
    if shot_de > enums.SHOT_DE_MAX:
        v.append("镜头间 ΔE %.1f > %.0f" % (shot_de, enums.SHOT_DE_MAX))
    if skin_de > enums.SKIN_DE_MAX:
        v.append("肤色区域 ΔE %.1f > %.0f" % (skin_de, enums.SKIN_DE_MAX))
    return v
