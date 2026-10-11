"""M5 摄影生成（实现层）：调视频适配器（Mock）生成镜头。

确定性提示词由 P1-A 编译链（build_p1_a.py → prompt_pack）产出；本函数只负责「调视频模型」。
"""


def generate_shot(prompt, video_adapter, fingerprint=""):
    sub = video_adapter.submit({"prompt": prompt, "fingerprint": fingerprint})
    result = video_adapter.query(sub["task_id"])
    return {"prompt": prompt}, {"produced_keys": [result.get("result", {}).get("object_key", "mock/shot")]}
