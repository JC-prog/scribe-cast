export interface ModelInfo {
  size: string
  label: string
  hint: string
}

export interface LanguageInfo {
  code: string
  label: string
}

export interface UploadResponse {
  job_id: string
}

export interface ValidateModelResponse {
  job_id: string
}

export type JobRqStatus =
  | 'queued'
  | 'started'
  | 'finished'
  | 'failed'
  | 'deferred'
  | 'scheduled'
  | 'stopped'
  | 'canceled'

export type PipelineStage =
  | 'queued'
  | 'downloading'
  | 'loading_model'
  | 'extracting_audio'
  | 'transcribing'
  | 'aligning'
  | 'writing_subtitles'
  | 'completed'
  | 'failed'

export interface TimingsMs {
  model_load?: number
  audio_extract?: number
  transcribe?: number
  align?: number
  srt_write?: number
  total?: number
}

export interface JobMeta {
  stage?: PipelineStage
  model_size?: string
  language?: string | null
  translate?: boolean
  detected_language?: string | null
  source_filename?: string
  source_url?: string | null
  batch_id?: string | null
  timings_ms?: TimingsMs
  device_used?: 'cpu' | 'cuda'
  fallback_occurred?: boolean
  error?: string | null
  output_path?: string | null
}

export interface JobStatusResponse {
  job_id: string
  status: JobRqStatus
  meta: JobMeta
  result: Record<string, unknown> | null
  error: string | null
  enqueued_at: string | null
  started_at: string | null
  ended_at: string | null
}

export interface BatchStatusResponse {
  batch_id: string
  jobs: JobStatusResponse[]
}

export interface JobListResponse {
  jobs: JobStatusResponse[]
}

export interface DiscoveredVideo {
  absolute_path: string
  relative_path: string
  size_bytes: number
  existing_srt: boolean
}

export interface FolderScanResponse {
  videos: DiscoveredVideo[]
}

export interface FolderTranscribeResponse {
  batch_id: string
  job_ids: string[]
}

export type VadMethod = 'silero' | 'pyannote'

export interface RuntimeSettings {
  batch_size: number
  chunk_size: number
  beam_size: number | null
  temperature: number | null
  condition_on_previous_text: boolean | null
  vad_method: VadMethod
  hf_token_set: boolean
  max_chars_per_cue: number
  max_seconds_per_cue: number
}

export interface RuntimeSettingsUpdate {
  batch_size?: number
  chunk_size?: number
  beam_size?: number | null
  temperature?: number | null
  condition_on_previous_text?: boolean | null
  vad_method?: VadMethod
  hf_token?: string
  max_chars_per_cue?: number
  max_seconds_per_cue?: number
}
