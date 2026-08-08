# Usage

## Upload a video

1. Open the **Upload video** tab.
2. Drag a video onto the dropzone, or click it to browse for a file.
3. Pick a **model** size and a **language** (or leave it on Auto-detect).
4. Click **Transcribe**.

Behind the scenes, clicking Transcribe first triggers a model-load check (`POST /api/models/validate`). If the model can't load — for example, a GPU was requested but the driver/toolkit isn't set up, or the model is too large for available memory — you'll see a warning banner instead of a silent hang or failed job. If the model loads but had to fall back from GPU to CPU, you'll see an informational banner but the job proceeds.

Once the model check passes, the video uploads and a progress indicator shows the current stage:

`Queued → Loading model → Extracting audio → Transcribing → Writing subtitles → Completed`

When it finishes, a completion overlay shows **how long transcription took** and a **Download subtitle** button.

## Folder batch

1. Open the **Batch folder** tab.
2. Enter a folder path and click **Scan**.
3. Select which discovered videos to transcribe (or use *Select all*). Videos that already have a sibling `.srt` are flagged.
4. Pick a model and language, then click **Transcribe N videos**.
5. Each video gets its own progress row; the `.srt` is written next to its source video.

### The `/data/...` path requirement

The folder-batch flow needs the **worker container** to see the exact filesystem path you type in. Because of that, folder paths must be given as container-visible paths under `/data/...` — that's where your host's `DATA_DIR` (set in `.env`) is bind-mounted.

For example, if `.env` has:

```
DATA_DIR=D:\Videos
```

and you have `D:\Videos\learning\lecture1.mp4` on your host, you'd scan `/data` or `/data/learning` in the UI. The resulting subtitle is written back to `D:\Videos\learning\lecture1.srt` on the host — right next to the source video.

### Search depth

Folder scanning looks at the folder itself **plus one level of subfolders** — not deeper. E.g. scanning `/data/learning` finds videos directly in `learning/` and in any immediate subfolder of it, but not in `learning/2024/january/`.

## Models

| Size | Notes |
|---|---|
| `tiny` | Fastest, lowest accuracy, ~1GB VRAM |
| `base` | Fast, ~1GB VRAM |
| `small` | Balanced speed/accuracy, ~2GB VRAM |
| `medium` | Higher accuracy, ~5GB VRAM |
| `large-v3` | Best accuracy, slowest, ~10GB VRAM |

The first time a given model size is used, it's downloaded from Hugging Face and cached (`model_cache` Docker volume) — subsequent loads of the same size are fast. The worker keeps one loaded model warm in memory at a time; switching model sizes between jobs triggers a reload.
