import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const TEST_CLIP = path.join(__dirname, 'fixtures', 'test_clip.mp4')

test('a completed upload job appears in History with a working download link', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('scribe-cast')).toBeVisible()

  await page.locator('select').first().selectOption('tiny')
  await page.locator('input[type=file]').setInputFiles(TEST_CLIP)
  await page.getByRole('button', { name: 'Transcribe' }).click()

  const overlay = page.locator('.overlay-card')
  await expect(overlay.getByText('Transcription complete')).toBeVisible({ timeout: 60_000 })
  await overlay.getByRole('button', { name: 'Close' }).last().click()

  await page.getByRole('button', { name: 'History' }).click()

  const row = page.locator('.history-row', { hasText: 'test_clip.mp4' }).first()
  await expect(row).toBeVisible({ timeout: 15_000 })
  await expect(row.getByText('Done')).toBeVisible()

  const downloadHref = await row.locator('.history-actions a').getAttribute('href')
  expect(downloadHref).toMatch(/^\/api\/download\//)
})
