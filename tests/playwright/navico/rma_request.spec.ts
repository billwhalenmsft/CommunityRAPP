/**
 * Navico — RMA Request scenario
 * Persona: Consumer (Alex Chen, recreational boater)
 */

import { test } from '@playwright/test';
import {
  runScenarioTurns,
  saveTestResult,
  TestResult,
  ChatMessage,
} from '../helpers/chat_helper';

const CHAT_URL = process.env.NAVICO_CHAT_URL ?? '';

test.describe('Navico — RMA Request @navico', () => {
  test.skip(!CHAT_URL, 'Set NAVICO_CHAT_URL to run this test');

  test('Consumer can initiate RMA for defective chartplotter', async ({ page }) => {
    const startMs = Date.now();
    let conversation: ChatMessage[] = [];

    await page.goto(CHAT_URL);
    await page.waitForLoadState('networkidle');

    conversation = await runScenarioTurns(page, [
      {
        user_says: 'I need to return a defective product',
        bot_should_contain: ['return', 'exchange', 'rma'],
      },
      {
        user_says: 'Simrad NSS12 evo3S — the touchscreen is unresponsive',
        bot_should_contain: ['serial', 'model', 'number'],
      },
      {
        user_says: 'SN-2022-NSS12-88432',
        bot_should_contain: ['warranty', 'ship', 'replacement'],
      },
      {
        user_says: 'Yes, please send me a replacement',
        wait_ms: 3000,
      },
    ]);

    const result: TestResult = {
      customer: 'navico',
      scenario_id: 'navico_rma_request',
      scenario_title: 'RMA Exchange Request',
      persona: 'consumer',
      status: 'pass',
      conversation,
      duration_ms: Date.now() - startMs,
      timestamp: new Date().toISOString(),
    };

    saveTestResult(result);
  });
});
