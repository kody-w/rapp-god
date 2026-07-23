#!/usr/bin/env node
// Validate one candidate frame against the current published head before append.

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { digestPayload, sha256Hex, FRAMES_DIR } from "./_frame.mjs";

export const SEALED_LEXICON_SHA = "c7c10ecba56e02eabc86bf178e9d2134cba8ce50338abc3d4d2e5ff2ef4bd51f";

const HEX64 = /^[0-9a-f]{64}$/;
const EMAIL = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i;
const RESTRICTED_MAIL_MARKER = /@(microsoft|gmail)\b/i;
const PRIVATE_IDENTIFIER = new RegExp(["kowi", "ldfe"].join(""), "i");
const NULL_STRING_ARTIFACT = /\b(?:undefined|null)\b/i;
const OWNER_SLUG_RAPPID = /rappid:@([A-Za-z0-9][A-Za-z0-9-]*)\/([A-Za-z0-9._-]+):([0-9a-fA-F]{64})(?![0-9a-fA-F])/g;

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function hasOwn(value, key) {
  return isObject(value) && Object.prototype.hasOwnProperty.call(value, key);
}

function validateIndex(index) {
  if (!isObject(index)) return { error: "chain: frames/index.json must contain an object" };
  if (!isObject(index.head)) return { error: "chain: frames/index.json has no current head" };
  if (!Number.isInteger(index.head.seq)) return { error: "chain: frames/index.json head.seq must be an integer" };
  if (!HEX64.test(index.head.sha256 || "")) return { error: "chain: frames/index.json head.sha256 must be 64 lowercase hex characters" };
  return { index };
}

function readIndex(indexPath) {
  try {
    return validateIndex(JSON.parse(fs.readFileSync(indexPath, "utf8")));
  } catch (error) {
    return { error: `chain: cannot read valid frames/index.json (${error.message})` };
  }
}

function collectEventStrings(value, fieldPath, strings) {
  if (typeof value === "string") {
    strings.push({ value, fieldPath });
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => collectEventStrings(item, `${fieldPath}[${index}]`, strings));
    return;
  }
  if (isObject(value)) {
    for (const [key, item] of Object.entries(value)) {
      collectEventStrings(item, `${fieldPath}.${key}`, strings);
    }
  }
}

function checkLexicon(payload, events, reasons) {
  const acceptablePins = new Set([SEALED_LEXICON_SHA]);

  events.forEach((event, index) => {
    if (!isObject(event) || event.type !== "lexicon-amendment") return;
    const eventPath = `payload.events[${index}]`;
    if (!HEX64.test(event.previous_sha || "") || !HEX64.test(event.new_sha || "")) {
      reasons.push(`lexicon pin: ${eventPath} requires 64-character lowercase-hex previous_sha and new_sha`);
      return;
    }
    if (!acceptablePins.has(event.previous_sha)) {
      reasons.push(`lexicon pin: ${eventPath}.previous_sha ${event.previous_sha} does not match the sealed v1 pin ${SEALED_LEXICON_SHA} or an earlier amendment in this frame`);
      return;
    }
    acceptablePins.add(event.new_sha);
  });

  if (hasOwn(payload, "lexicon_sha") && !acceptablePins.has(payload.lexicon_sha)) {
    reasons.push(`lexicon pin: payload.lexicon_sha ${JSON.stringify(payload.lexicon_sha)} must equal sealed v1 ${SEALED_LEXICON_SHA}, unless it is the new_sha of a valid lexicon-amendment event`);
  }
}

function checkCensus(payload, events, reasons) {
  const census = payload.census;
  if (!isObject(census)) {
    reasons.push("census honesty: payload.census must be present");
    return;
  }
  if (!Array.isArray(census.repos) || census.repos.length === 0) {
    reasons.push("census honesty: payload.census.repos must contain at least one repository");
    return;
  }

  const gapEvents = events.filter((event) => isObject(event) && event.type === "observation-gap");
  const gapSources = new Set(gapEvents.map((event) => event.source).filter((source) => typeof source === "string"));
  const unreadableSources = new Map();
  const markUnreadable = (source, fieldPath) => {
    if (!unreadableSources.has(source)) unreadableSources.set(source, fieldPath);
  };

  const homes = payload.skeleton?.homes;
  if (isObject(homes)) {
    for (const [name, home] of Object.entries(homes)) {
      if (isObject(home) && home.present === false) {
        markUnreadable(`spec-home:${name}`, `payload.skeleton.homes.${name}.present`);
      }
    }
  }

  const spine = payload.skeleton?.spine;
  if (isObject(spine)) {
    if (hasOwn(spine, "registry_sha256") && spine.registry_sha256 === null) {
      markUnreadable("spine:registry", "payload.skeleton.spine.registry_sha256");
    }
    if (hasOwn(spine, "foundation_sha256") && spine.foundation_sha256 === null) {
      markUnreadable("spine:foundation", "payload.skeleton.spine.foundation_sha256");
    }
  }

  census.repos.forEach((repo, index) => {
    if (!isObject(repo)) return;
    const unreadable = repo.status === "unreadable"
      || repo.status === "stale"
      || repo.head_stale === true
      || (repo.stale === true && repo.status !== "absent_unconfirmed");
    if (!unreadable) return;
    const source = typeof repo.owner === "string" && typeof repo.name === "string"
      ? `repo:${repo.owner}/${repo.name}`
      : `repo-entry:${index}`;
    markUnreadable(source, `payload.census.repos[${index}]`);
  });

  if (hasOwn(payload.vitals, "drift_issues") && payload.vitals.drift_issues === null) {
    markUnreadable("drift-issues", "payload.vitals.drift_issues");
  }

  for (const [source, fieldPath] of unreadableSources) {
    if (!gapSources.has(source)) {
      reasons.push(`census honesty: ${fieldPath} marks ${source} unreadable but payload.events has no matching observation-gap`);
    }
  }

  if (typeof census.transport_unreadable === "number" && census.transport_unreadable > 0) {
    const transportGaps = gapEvents.filter((event) => event.transport === true).length;
    if (transportGaps < census.transport_unreadable) {
      reasons.push(`census honesty: payload.census.transport_unreadable is ${census.transport_unreadable}, but only ${transportGaps} transport observation-gap event(s) are present`);
    }
  }
}

function checkEventDriftClasses(events, reasons) {
  events.forEach((event, index) => {
    if (isObject(event) && typeof event.text === "string" && NULL_STRING_ARTIFACT.test(event.text)) {
      reasons.push(`drift-class name-collision-unnamed: payload.events[${index}].text contains an undefined/null string artifact`);
    }

    const strings = [];
    collectEventStrings(event, `payload.events[${index}]`, strings);
    for (const { value, fieldPath } of strings) {
      for (const match of value.matchAll(OWNER_SLUG_RAPPID)) {
        const [, owner, slug, suffix] = match;
        const illegalSuffix = sha256Hex(`${owner}/${slug}`);
        if (suffix.toLowerCase() === illegalSuffix) {
          reasons.push(`drift-class rappid-invariant-violation: ${fieldPath} contains a rappid derived from sha256("${owner}/${slug}")`);
        }
      }

      if (EMAIL.test(value)) {
        reasons.push(`drift-class private-name-leak: ${fieldPath} contains an email address`);
      } else if (RESTRICTED_MAIL_MARKER.test(value)) {
        reasons.push(`drift-class private-name-leak: ${fieldPath} contains an @microsoft/@gmail identifier`);
      }
      if (PRIVATE_IDENTIFIER.test(value)) {
        reasons.push(`drift-class private-name-leak: ${fieldPath} contains the prohibited private identifier pattern`);
      }
    }
  });
}

export function validateCandidate(candidate, options = {}) {
  const reasons = [];
  const indexPath = options.indexPath || path.join(FRAMES_DIR, "index.json");
  const loaded = hasOwn(options, "index") ? validateIndex(options.index) : readIndex(indexPath);
  const head = loaded.index?.head || null;

  if (loaded.error) reasons.push(loaded.error);
  if (!isObject(candidate)) {
    reasons.push("candidate: top-level JSON value must be an object");
    return { allowed: false, reasons, head, candidateSeq: null };
  }

  if (head) {
    const expectedSeq = head.seq + 1;
    if (candidate.seq !== expectedSeq) {
      reasons.push(`chain: candidate.seq ${JSON.stringify(candidate.seq)} must equal head.seq + 1 (${expectedSeq})`);
    }
    if (candidate.parent_sha !== head.sha256) {
      reasons.push(`chain: candidate.parent_sha ${JSON.stringify(candidate.parent_sha)} must equal current head sha256 ${head.sha256}`);
    }
  }

  if (!isObject(candidate.payload)) {
    reasons.push("integrity: candidate.payload must be an object");
  } else {
    const recomputed = digestPayload(candidate.payload);
    if (candidate.sha256 !== recomputed) {
      reasons.push(`integrity: candidate.sha256 ${JSON.stringify(candidate.sha256)} does not match recomputed payload sha256 ${recomputed}`);
    }

    const events = Array.isArray(candidate.payload.events) ? candidate.payload.events : [];
    checkLexicon(candidate.payload, events, reasons);
    checkCensus(candidate.payload, events, reasons);
    checkEventDriftClasses(events, reasons);
  }

  return {
    allowed: reasons.length === 0,
    reasons,
    head,
    candidateSeq: candidate.seq,
    candidateSha256: candidate.sha256,
  };
}

export function validateCandidateFile(candidatePath, options = {}) {
  let candidate;
  try {
    candidate = JSON.parse(fs.readFileSync(path.resolve(candidatePath), "utf8"));
  } catch (error) {
    return {
      allowed: false,
      reasons: [`candidate: cannot read valid JSON from ${candidatePath} (${error.message})`],
      head: null,
      candidateSeq: null,
    };
  }
  return validateCandidate(candidate, options);
}

export function printGateResult(result) {
  if (result.allowed) {
    console.log(`APPEND ALLOWED: candidate seq ${result.candidateSeq} extends head seq ${result.head.seq}; pre-append frame gate passed`);
    return;
  }
  console.error(`APPEND REFUSED: pre-append frame gate found ${result.reasons.length} reason(s)`);
  for (const reason of result.reasons) console.error(`  - ${reason}`);
}

function main() {
  const args = process.argv.slice(2);
  if (args.length !== 1) {
    const result = {
      allowed: false,
      reasons: ["usage: node tools/frame-gate.mjs <candidate-frame.json>"],
      head: null,
      candidateSeq: null,
    };
    printGateResult(result);
    process.exitCode = 2;
    return;
  }

  const result = validateCandidateFile(args[0]);
  printGateResult(result);
  process.exitCode = result.allowed ? 0 : 1;
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) main();
