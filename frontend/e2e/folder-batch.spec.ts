import { expect, test } from '@playwright/test'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const FIXTURE = path.join(__dirname, 'fixtures', 'test_clip.mp4')

// This test needs a video sitting in the folder bind-mounted to /data in the
// api/worker containers (see docker-compose.yml's DATA_DIR mount). Point
// E2E_DATA_DIR at that same host folder — defaults to ../data relative to
// this file, matching docker-compose.yml's default `./data`.
const DATA_DIR = process.env.E2E_DATA_DIR ?? path.join(__dirname, '..', '..', 'data')
const FIXTURE_NAME = 'e2e_folder_batch_test_clip.mp4'
const copiedVideoPath = path.join(DATA_DIR, FIXTURE_NAME)
const generatedSrtPath = path.join(DATA_DIR, FIXTURE_NAME.replace(/\.mp4$/, '.srt'))

test.beforeAll(async () => {
  await fs.mkdir(DATA_DIR, { recursive: true })
  await fs.copyFile(FIXTURE, copiedVideoPath)
})

test.afterAll(async () => {
  await fs.rm(copiedVideoPath, { force: true })
  await fs.rm(generatedSrtPath, { force: true })
})

test('scans a folder, runs a batch, and shows per-video completion', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Batch folder' }).click()

  await page.getByPlaceholder('/data/your-folder').fill('/data')
  await page.getByRole('button', { name: 'Scan' }).click()

  await expect(page.getByText(FIXTURE_NAME)).toBeVisible({ timeout: 15_000 })

  await page.locator('select').first().selectOption('tiny')
  await page.getByRole('button', { name: /Transcribe \d+ video/ }).click()

  const progressRow = page.locator('.job-progress', { hasText: FIXTURE_NAME })
  await expect(progressRow.getByText('Done')).toBeVisible({ timeout: 60_000 })
  await expect(progressRow.getByText(/Took/)).toBeVisible()
})
