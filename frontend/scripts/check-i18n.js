#!/usr/bin/env node
/**
 * check-i18n.js
 *
 * Compares ko.json (source of truth) with en.json and reports any missing
 * or extra keys. Supports nested objects and arrays.
 *
 * Usage:  node scripts/check-i18n.js
 * Exit 0 if all keys match, exit 1 if there are mismatches.
 */

import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const koPath = resolve(__dirname, "../src/i18n/locales/ko.json");
const enPath = resolve(__dirname, "../src/i18n/locales/en.json");

const ko = JSON.parse(readFileSync(koPath, "utf-8"));
const en = JSON.parse(readFileSync(enPath, "utf-8"));

/**
 * Recursively collect all dot-notation keys from an object.
 * Arrays are treated as leaf values (not iterated key-by-key).
 */
function collectKeys(obj, prefix = "") {
  const keys = [];
  for (const [key, value] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (
      value !== null &&
      typeof value === "object" &&
      !Array.isArray(value)
    ) {
      keys.push(...collectKeys(value, path));
    } else {
      keys.push(path);
    }
  }
  return keys;
}

const koKeys = new Set(collectKeys(ko));
const enKeys = new Set(collectKeys(en));

const missingInEn = [...koKeys].filter((k) => !enKeys.has(k));
const extraInEn = [...enKeys].filter((k) => !koKeys.has(k));

let exitCode = 0;

if (missingInEn.length > 0) {
  console.error(`\n  Missing in en.json (${missingInEn.length} keys):`);
  missingInEn.forEach((k) => console.error(`    - ${k}`));
  exitCode = 1;
}

if (extraInEn.length > 0) {
  console.warn(`\n  Extra in en.json (not in ko.json) (${extraInEn.length} keys):`);
  extraInEn.forEach((k) => console.warn(`    + ${k}`));
  // Extra keys are warnings, not errors
}

if (exitCode === 0 && extraInEn.length === 0) {
  console.log("  i18n check passed: ko.json and en.json keys are in sync.");
}

process.exit(exitCode);
