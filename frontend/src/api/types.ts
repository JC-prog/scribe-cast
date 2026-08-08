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
  | 'loading_model'
  | 'extracting_audio'
  | 'transcribing'
  | 'writing_subtitles'
  | 'completed'
  | 'failed'

export interface TimingsMs {
  model_load?: number
  audio_extract?: number
  transcribe?: number
  srt_write?: number
  total?: number
}

export interface JobMeta {
  stage?: PipelineStage
  model_size?: string
  language?: string | null
  detected_language?: string | null
  source_filename?: string
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
}

export interface BatchStatusResponse {
  batch_id: string
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
