# Features

## Single upload → subtitle download

Upload a video through the browser; scribe-cast transcribes it and offers the resulting `.srt` for download. The completion overlay reports the total time taken, sourced from the backend's own timing (not a client-side stopwatch, so it stays accurate even if the browser tab is backgrounded/throttled).

## Folder batch transcription

Point scribe-cast at a folder and it recursively finds videos in that folder plus one level of subfolders. You choose which of the discovered videos to process — individually or via *Select all* — and each selected video is transcribed independently, with its `.srt` written next to the source file. See [Usage → Folder batch](usage.md#folder-batch) for the container path-mapping details.

Each video in a batch runs as its own job, so:

- Progress is visible per-video, not just for the batch as a whole.
- One video failing (corrupt file, unsupported codec) doesn't block the rest of the batch.

## Model selection with a load pre-check

Before committing to a full transcription job, scribe-cast tries to actually load the selected model and reports back whether it worked — rather than letting a job fail deep into processing because the model couldn't be loaded (out of memory, missing weights, unsupported device). See [Architecture → Model manager](architecture.md#model-manager-the-load-pre-check) for how this is implemented.

## Language selection

Pick a target language from the Whisper-supported list, or leave it on **Auto-detect** and let the model infer it. The detected (or specified) language is shown once transcription completes.

## CPU/GPU portability

The exact same worker Docker image runs on a machine with an NVIDIA GPU or a CPU-only machine:

- `DEVICE=auto` (the default) uses a GPU if one is actually available, otherwise CPU.
- `DEVICE=cuda` (used by `docker-compose.gpu.yml`) requests a GPU; if none is available at runtime, it **falls back to CPU automatically** rather than failing, and this fallback is surfaced in both the logs and the UI (a warning banner).

See [Architecture → CPU/GPU portability](architecture.md#cpugpu-portability) for the full design.

## Observability

- Structured JSON logs in `./logs/` on the host: `api.log`, `worker.log`, `errors.log`.
- Each transcription job records per-stage timing: model load, audio extraction, transcription, subtitle writing, and total — visible both in the logs and (for the total) in the completion overlay / per-video progress rows.
- Errors are logged with context (job id, model, stage) rather than just a stack trace.
