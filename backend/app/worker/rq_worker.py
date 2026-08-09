"""
Entry point: `python -m app.worker.rq_worker`.

Must run as SimpleWorker (no per-job fork). RQ's default Worker forks a
child process per job for crash isolation; a module-level ModelManager
cache loaded in a forked child is lost when that child exits, defeating
the whole point of caching a loaded model between jobs. Acceptable
trade-off for a trusted, single-tenant, local-first tool.
"""

from redis import Redis
from rq import Queue, SimpleWorker
from rq.timeouts import TimerDeathPenalty

from app.config import settings
from app.logging_config import get_logger, log_event, setup_logging


class PortableSimpleWorker(SimpleWorker):
    """
    TimerDeathPenalty (thread-based) instead of RQ's default signal-based
    UnixSignalDeathPenalty: SIGALRM doesn't exist on Windows, and this needs
    to run there for local (non-Docker) development, not just inside Linux
    containers.
    """

    death_penalty_class = TimerDeathPenalty


def main() -> None:
    setup_logging("worker")
    logger = get_logger("scribecast.worker")

    connection = Redis.from_url(settings.redis_url)
    queue = Queue(settings.queue_name, connection=connection)

    log_event(
        logger, "worker_starting", version=settings.app_version, queue=settings.queue_name, redis_url=settings.redis_url
    )
    worker = PortableSimpleWorker([queue], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
