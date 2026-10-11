"""PG 专属队列 SQL（SKIP LOCKED 抢占，联调阶段用真实 PG 测并发）。

对齐 docs/designs/任务编排设计.md §二/§六；SQLite 无 SKIP LOCKED，故此处 SQL 仅供 PG 使用。
"""
CLAIM_SQL = """
UPDATE jobs SET status='running', locked_until=:now + :lease,
                lease_epoch=lease_epoch+1, attempts=attempts+1
WHERE id = (SELECT id FROM jobs
            WHERE status='queued' AND available_at <= :now
            ORDER BY priority DESC, id ASC
            FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING *;
"""

HEARTBEAT_SQL = """
UPDATE jobs SET locked_until=:now + :lease
WHERE id=:job_id AND lease_epoch=:epoch;
"""

RECLAIM_SQL = """
SELECT id, checkpoint, attempts, attempt_limit FROM jobs
WHERE status='running' AND locked_until < :now
ORDER BY id ASC;
"""
