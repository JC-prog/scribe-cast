from app.worker.job_meta import update_job_meta


class FakeJob:
    def __init__(self):
        self.meta = {"stage": "queued"}
        self.save_meta_calls = 0

    def save_meta(self):
        self.save_meta_calls += 1


def test_update_job_meta_merges_fields_and_saves():
    job = FakeJob()

    update_job_meta(job, stage="transcribing", model_size="tiny")

    assert job.meta == {"stage": "transcribing", "model_size": "tiny"}
    assert job.save_meta_calls == 1


def test_update_job_meta_preserves_untouched_keys():
    job = FakeJob()
    job.meta["source_filename"] = "video.mp4"

    update_job_meta(job, stage="completed")

    assert job.meta == {"stage": "completed", "source_filename": "video.mp4"}
