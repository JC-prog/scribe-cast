import type {
  BatchStatusResponse,
  FolderScanResponse,
  FolderTranscribeResponse,
  JobStatusResponse,
  LanguageInfo,
  ModelInfo,
  UploadResponse,
  ValidateModelResponse,
} from './types'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body && typeof body === 'object' && 'detail' in body ? String(body.detail) : response.statusText
    throw new ApiError(response.status, detail)
  }
  return response.json() as Promise<T>
}

function postJson<T>(path: string, payload: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getModels(): Promise<{ models: ModelInfo[] }> {
  return request('/api/models')
}

export function getLanguages(): Promise<{ languages: LanguageInfo[] }> {
  return request('/api/languages')
}

export function validateModel(modelSize: string): Promise<ValidateModelResponse> {
  return postJson('/api/models/validate', { model_size: modelSize })
}

export function uploadVideo(
  file: File,
  modelSize: string,
  language: string,
  translate: boolean,
): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('model_size', modelSize)
  formData.append('language', language)
  formData.append('translate', String(translate))
  return request('/api/upload', { method: 'POST', body: formData })
}

export function transcribeUrl(
  url: string,
  modelSize: string,
  language: string,
  translate: boolean,
): Promise<UploadResponse> {
  return postJson('/api/url/transcribe', { url, model_size: modelSize, language, translate })
}

export function scanFolder(folderPath: string): Promise<FolderScanResponse> {
  return postJson('/api/folder/scan', { folder_path: folderPath })
}

export function startFolderBatch(
  folderPath: string,
  videoPaths: string[],
  modelSize: string,
  language: string,
  translate: boolean,
): Promise<FolderTranscribeResponse> {
  return postJson('/api/folder/transcribe', {
    folder_path: folderPath,
    video_paths: videoPaths,
    model_size: modelSize,
    language,
    translate,
  })
}

export function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return request(`/api/jobs/${jobId}`)
}

export function getBatchStatus(batchId: string): Promise<BatchStatusResponse> {
  return request(`/api/jobs/batch/${batchId}`)
}

export function downloadUrl(jobId: string): string {
  return `/api/download/${jobId}`
}
