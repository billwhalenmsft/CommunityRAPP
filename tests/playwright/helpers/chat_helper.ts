/**
 * Shared helpers for Mfg CoE Playwright tests.
 * Supports Copilot Studio webchat, D365 portals, and Teams webchat surfaces.
 */

import { Page, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

export interface ChatMessage {
  role: 'user' | 'bot';
  text: string;
  timestamp?: string;
}

export interface TestResult {
  customer: string;
  scenario_id: string;
  scenario_title: string;
  persona: string;
  status: 'pass' | 'fail' | 'partial';
  conversation: ChatMessage[];
  failure_reason?: string;
  screenshot_path?: string;
  duration_ms: number;
  timestamp: string;
}

// ── Surface-specific selectors ──────────────────────────────────────────────

export const SELECTORS = {
  copilotStudio: {
    chatInput: '[data-testid="webchat__send-box__main"] textarea, .webchat__send-box textarea',
    sendButton: '[data-testid="webchat__send-box__button"], button[aria-label="Send"]',
    botMessage: '.webchat__bubble--from-bot .webchat__bubble__content, [data-activity-role="bot"] .webchat__render-markdown',
    userMessage: '.webchat__bubble--from-user .webchat__bubble__content',
    typingIndicator: '.webchat__typing-indicator',
  },
  d365Portal: {
    chatInput: '#chat-widget-input, [aria-label*="chat"], .chat-input textarea',
    sendButton: '.chat-send-btn, button[aria-label*="Send"]',
    botMessage: '.bot-message, .chat-message.bot',
    userMessage: '.user-message, .chat-message.user',
    typingIndicator: '',
  },
  teams: {
    chatInput: '.ql-editor[contenteditable="true"]',
    sendButton: 'button[aria-label="Send"]',
    botMessage: '.ts-message-list-item--incoming .ts-message-renderPlainText',
    userMessage: '.ts-message-list-item--outgoing .ts-message-renderPlainText',
    typingIndicator: '',
  },
};

// ── Core chat helpers ────────────────────────────────────────────────────────

export async function sendChatMessage(
  page: Page,
  message: string,
  surface: keyof typeof SELECTORS = 'copilotStudio'
): Promise<void> {
  const sel = SELECTORS[surface];
  const input = page.locator(sel.chatInput).first();
  await input.click();
  await input.fill(message);
  await page.locator(sel.sendButton).first().click();
}

export async function waitForBotResponse(
  page: Page,
  previousCount: number,
  surface: keyof typeof SELECTORS = 'copilotStudio',
  timeoutMs = 30000
): Promise<string> {
  const sel = SELECTORS[surface];

  // Wait for typing indicator to appear then disappear
  if (sel.typingIndicator) {
    try {
      await page.locator(sel.typingIndicator).waitFor({ state: 'visible', timeout: 5000 });
      await page.locator(sel.typingIndicator).waitFor({ state: 'hidden', timeout: timeoutMs });
    } catch {
      // typing indicator may not appear — fall through
    }
  }

  // Wait for new bot message
  await expect(page.locator(sel.botMessage)).toHaveCount(previousCount + 1, { timeout: timeoutMs });
  const messages = await page.locator(sel.botMessage).all();
  return (await messages[messages.length - 1].textContent()) ?? '';
}

export async function getBotMessageCount(
  page: Page,
  surface: keyof typeof SELECTORS = 'copilotStudio'
): Promise<number> {
  return page.locator(SELECTORS[surface].botMessage).count();
}

// ── Scenario runner ──────────────────────────────────────────────────────────

export interface ScenarioTurn {
  user_says: string;
  bot_should_contain?: string[];
  wait_ms?: number;
}

export async function runScenarioTurns(
  page: Page,
  turns: ScenarioTurn[],
  surface: keyof typeof SELECTORS = 'copilotStudio'
): Promise<ChatMessage[]> {
  const conversation: ChatMessage[] = [];

  for (const turn of turns) {
    const priorCount = await getBotMessageCount(page, surface);

    await sendChatMessage(page, turn.user_says, surface);
    conversation.push({ role: 'user', text: turn.user_says, timestamp: new Date().toISOString() });

    if (turn.wait_ms) {
      await page.waitForTimeout(turn.wait_ms);
    }

    const botText = await waitForBotResponse(page, priorCount, surface);
    conversation.push({ role: 'bot', text: botText, timestamp: new Date().toISOString() });

    // Validate expected content
    if (turn.bot_should_contain) {
      for (const expected of turn.bot_should_contain) {
        expect(botText.toLowerCase()).toContain(expected.toLowerCase());
      }
    }
  }

  return conversation;
}

// ── Result logging ───────────────────────────────────────────────────────────

export function saveTestResult(result: TestResult): void {
  const resultsDir = path.join(__dirname, '../../../customers/mfg_coe/test_results');
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }

  // Append to daily results JSONL file
  const dateStr = new Date().toISOString().split('T')[0];
  const resultsFile = path.join(resultsDir, `results_${dateStr}.jsonl`);
  fs.appendFileSync(resultsFile, JSON.stringify(result) + '\n');

  // Update latest summary
  const summaryFile = path.join(resultsDir, 'latest_summary.json');
  let summary: Record<string, TestResult[]> = {};
  if (fs.existsSync(summaryFile)) {
    try {
      summary = JSON.parse(fs.readFileSync(summaryFile, 'utf8'));
    } catch {
      summary = {};
    }
  }
  if (!summary[result.customer]) summary[result.customer] = [];
  summary[result.customer].push(result);
  fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));
}

export function loadScenarios(customer: string): Record<string, unknown>[] {
  const scenarioFile = path.join(
    __dirname,
    `../../../customers/mfg_coe/testing/${customer}/scenarios.json`
  );
  if (!fs.existsSync(scenarioFile)) {
    throw new Error(`No scenarios found for customer: ${customer}`);
  }
  return JSON.parse(fs.readFileSync(scenarioFile, 'utf8'));
}

export function loadPersonas(customer: string): Record<string, unknown>[] {
  const personaFile = path.join(
    __dirname,
    `../../../customers/mfg_coe/testing/${customer}/personas.json`
  );
  if (!fs.existsSync(personaFile)) {
    throw new Error(`No personas found for customer: ${customer}`);
  }
  return JSON.parse(fs.readFileSync(personaFile, 'utf8'));
}
