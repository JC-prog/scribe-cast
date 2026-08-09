from typing import Literal

from pydantic import BaseModel, Field


class RuntimeSettings(BaseModel):
    """
    Admin-tunable WhisperX behavior + subtitle formatting, persisted as a
    single JSON blob in Redis (see app/core/runtime_settings.py) rather than
    env vars, so it can change without a container restart. Defaults here
    match what was previously hardcoded, so out-of-the-box behavior is
    unchanged until someone actually opens the admin panel.
    """

    batch_size: int = Field(16, ge=1, le=128)
    chunk_size: int = Field(30, ge=1, le=120)
    # None = don't override, let whisperx/faster-whisper use its own
    # internal default rather than asserting a guessed value here.
    beam_size: int | None = Field(None, ge=1, le=20)
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    condition_on_previous_text: bool | None = None
    # "silero" is the default deliberately - lower friction, no token
    # needed. "pyannote" is nominally a gated Hugging Face model, though
    # verified against a real run that in the currently pinned whisperx
    # version its VAD checkpoint actually ships bundled in the whisperx
    # package itself, so hf_token isn't strictly required for VAD alone in
    # practice - kept configurable anyway since that's a version-specific
    # implementation detail, not a documented guarantee.
    vad_method: Literal["silero", "pyannote"] = "silero"
    hf_token: str | None = None
    max_chars_per_cue: int = Field(84, ge=10, le=500)
    max_seconds_per_cue: float = Field(7.0, gt=0, le=60.0)


class RuntimeSettingsUpdate(BaseModel):
    """
    Same fields as RuntimeSettings, all optional with no defaults. Combined
    server-side with `.model_dump(exclude_unset=True)` so only fields the
    client actually sent get merged onto the currently stored settings -
    critical for hf_token, where "not sent" must mean "leave unchanged",
    not "clear it".
    """

    batch_size: int | None = Field(None, ge=1, le=128)
    chunk_size: int | None = Field(None, ge=1, le=120)
    beam_size: int | None = Field(None, ge=1, le=20)
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    condition_on_previous_text: bool | None = None
    vad_method: Literal["silero", "pyannote"] | None = None
    hf_token: str | None = None
    max_chars_per_cue: int | None = Field(None, ge=10, le=500)
    max_seconds_per_cue: float | None = Field(None, gt=0, le=60.0)


class RuntimeSettingsResponse(BaseModel):
    """RuntimeSettings minus the raw hf_token - never echo a secret back to the client."""

    batch_size: int
    chunk_size: int
    beam_size: int | None
    temperature: float | None
    condition_on_previous_text: bool | None
    vad_method: Literal["silero", "pyannote"]
    hf_token_set: bool
    max_chars_per_cue: int
    max_seconds_per_cue: float

    @classmethod
    def from_settings(cls, settings: RuntimeSettings) -> "RuntimeSettingsResponse":
        return cls(
            batch_size=settings.batch_size,
            chunk_size=settings.chunk_size,
            beam_size=settings.beam_size,
            temperature=settings.temperature,
            condition_on_previous_text=settings.condition_on_previous_text,
            vad_method=settings.vad_method,
            hf_token_set=bool(settings.hf_token),
            max_chars_per_cue=settings.max_chars_per_cue,
            max_seconds_per_cue=settings.max_seconds_per_cue,
        )
