/**
 * Navico — Warranty Check scenario
 * Persona: Dealer Rep (Marcus Torres, authorized Navico dealer)
 *
 * Set environment variables before running:
 *   NAVICO_CHAT_URL — URL of the Copilot Studio webchat demo page
 */

import { test, expect } from '@playwright/test';
import {
  runScenarioTurns,
  saveTestResult,
  TestResult,
  ChatMessage,
} from '../helpers/chat_helper';

const CHAT_URL = process.env.NAVICO_CHAT_URL ?? '';

test.describe('Navico — Warranty Check @navico @smoke', () => {
  test.skip(!CHAT_URL, 'Set NAVICO_CHAT_URL to run this test');

  test('Dealer rep can check warranty status by serial number', async ({ page }) => {
    const startMs = Date.now();
    let conversation: ChatMessage[] = [];

    await page.goto(CHAT_URL);
    await page.waitForLoadState('networkidle');

    conversation = await runScenarioTurns(page, [
      {
        user_says: 'check warranty',
        bot_should_contain: ['serial', 'warranty'],
      },
      {
        user_says: 'SN-2024-NAVICO-001234',
        bot_should_contain: ['warranty', 'years'],
      },
      {
        user_says: 'No thanks, that covers it',
        wait_ms: 2000,
      },
    ]);

    const result: TestResult = {
      customer: 'navico',
      scenario_id: 'navico_warranty_check',
      scenario_title: 'Warranty Status Check',
      persona: 'dealer_rep',
      status: 'pass',
      conversation,
      duration_ms: Date.now() - startMs,
      timestamp: new Date().toISOString(),
    };

    saveTestResult(result);
  });
});
