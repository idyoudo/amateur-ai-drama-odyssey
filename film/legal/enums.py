"""M18 法律契约层 · 封闭枚举。"""

# 署名角色（M18.2-F01）
CREDIT_ROLES = ("writer", "story", "adaptation", "script_editor")
# 署名主体类型：限人类（AI 不得署名）
SUBJECT_TYPES = ("human",)

# AI 标识三类（M18.5-F02 / B-09/B-10）
LABEL_TYPES = ("explicit", "implicit", "export_file")

# 素材来源（M18.2-F02：AI 材料不计入 source material）
MATERIAL_ORIGINS = ("human", "ai")
