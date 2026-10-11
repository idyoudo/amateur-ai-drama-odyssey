"""worker 业务处理器：按 job.type 路由到模块实现层（无凭据走 Mock）。"""
from film.script import generate as script_gen
from film.suppliers import adapter as sup_adapter


def make_handler(model_config):
    """构建业务 handler：claim 后按 type 分发到各模块生成函数。"""
    def _adapter(kind):
        return sup_adapter.make_adapter(kind, model_config.get(kind, {}))

    adapters = {k: _adapter(k) for k in model_config}

    def handler(job):
        job_type = job.get("type") if isinstance(job, dict) else job.type
        if job_type in ("adapt", "script_revise"):
            _, cp = script_gen.generate_outline("默认 logline", adapters.get("text"))
            return cp
        # 其余 stage：占位（M3/M5/M7 等实现层随供应商凭据接入）
        return {"produced_keys": ["obj/%s" % job_type]}

    return handler
