import fakeredis
import pytest
from fastapi.testclient import TestClient
from rq import Queue

from app.api.deps import get_queue, get_redis_conn
from app.main import app


@pytest.fixture
def fake_redis_conn():
    return fakeredis.FakeStrictRedis()


@pytest.fixture
def fake_queue(fake_redis_conn):
    # is_async defaults to True: enqueue() just pushes to the fake queue, it
    # does not import/run the real task function (which would pull in
    # faster_whisper and attempt real ffmpeg/model work in a unit test).
    return Queue("transcription", connection=fake_redis_conn)


@pytest.fixture
def client(fake_redis_conn, fake_queue):
    app.dependency_overrides[get_redis_conn] = lambda: fake_redis_conn
    app.dependency_overrides[get_queue] = lambda: fake_queue
    yield TestClient(app)
    app.dependency_overrides.clear()
