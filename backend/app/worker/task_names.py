"""
Dotted paths to worker task functions, enqueued by string
(`queue.enqueue(TASK_X, ...)`) rather than by importing app.worker.tasks
directly. app.worker.tasks imports model_manager, which imports
faster_whisper/ctranslate2 — the API process must never pull those in, so
routes reference tasks by name; only the worker process resolves and
imports the real function when it executes a job.
"""

TASK_TRANSCRIBE_UPLOAD = "app.worker.tasks.task_transcribe_upload"
TASK_TRANSCRIBE_FOLDER_ITEM = "app.worker.tasks.task_transcribe_folder_item"
TASK_VALIDATE_MODEL = "app.worker.tasks.task_validate_model"
