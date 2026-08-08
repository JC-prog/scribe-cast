import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const TEST_CLIP = path.join(__dirname, 'fixtures', 'test_clip.mp4')

test('uploads a video and shows the completion overlay with elapsed time', async ({ page }) => {
  const consoleErrors: string[] = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })

  await page.goto('/')
  await expect(page.getByText('scribe-cast')).toBeVisible()

  await page.locator('select').first().selectOption('tiny')
  await page.locator('input[type=file]').setInputFiles(TEST_CLIP)

  await page.getByRole('button', { name: 'Transcribe' }).click()

  const overlay = page.locator('.overlay-card')
  await expect(overlay.getByText('Transcription complete')).toBeVisible({ timeout: 60_000 })
  await expect(overlay.getByText(/Took/)).toBeVisible()

  const downloadHref = await overlay.locator('.overlay-actions a').getAttribute('href')
  expect(downloadHref).toMatch(/^\/api\/download\//)

  expect(consoleErrors).toEqual([])
})
