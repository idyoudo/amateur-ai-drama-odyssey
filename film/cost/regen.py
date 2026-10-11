"""重生成预算（M14.2-F06：R = 单集成本上限 ÷ (镜头数 × 单镜生成成本)，超 R 强制转人工）。"""


def regen_budget(episode_cap, shot_count, shot_cost):
    """单集可用返工预算 R（超 R 禁止默认批量重发，E-34/E-28）。"""
    if shot_count <= 0 or shot_cost <= 0:
        return 0
    return int(episode_cap / (shot_count * shot_cost))
