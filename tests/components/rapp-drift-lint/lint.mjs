#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { lstat, readFile, readlink } from "node:fs/promises";
import path from "node:path";
import { TextDecoder } from "node:util";

const minimumNodeMajor = 20;
const oldRappidPattern = /rappid:v[23]:/i;
const legacyMarkerPattern = /(?:\blegacy\b|\bread[- ]forever\b|\bcanonicalized\b)/i;
const mintTeachPattern =
  /(?<![A-Za-z0-9])(?:mint(?:s|ed|ing)?|emit(?:s|ted|ting)?|teach(?:es|ing)?|taught|use(?:s|d)?|using|format(?:s|ted|ting)?|syntax|grammar|creat(?:e|es|ed|ing)|generat(?:e|es|ed|ing)|issu(?:e|es|ed|ing)|produc(?:e|es|ed|ing)|writ(?:e|es|ing|ten)|construct(?:s|ed|ing)?|assign(?:s|ed|ing)?|prefix|template|example|new)(?![A-Za-z0-9])/i;
const obsoletePlatformPattern = new RegExp(
  ["Prototyping", "Platform"].join(" "),
);
const workAccountPattern = new RegExp(["kowi", "ldfe"].join(""), "i");
const blockedEmailPattern = new RegExp(
  `[A-Z0-9._%+-]+@(?:${["micro", "soft"].join("")}|gmail)\\.com(?=$|[^A-Z0-9.-])`,
  "i",
);

function fail(message) {
  console.error(`drift-lint: ${message}`);
  process.exit(2);
}

function parseArguments(argv) {
  let target = ".";

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];

    if (argument === "--path") {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) {
        fail("--path requires a directory");
      }
      target = value;
      index += 1;
    } else if (argument === "--help" || argument === "-h") {
      console.log("Usage: node lint.mjs [--path <dir>]");
      process.exit(0);
    } else {
      fail(`unknown argument: ${argument}`);
    }
  }

  return path.resolve(target);
}

function runGit(directory, args, { allowFailure = false } = {}) {
  const result = spawnSync("git", ["-C", directory, ...args], {
    encoding: null,
    maxBuffer: 64 * 1024 * 1024,
  });

  if (result.error) {
    fail(`could not run git: ${result.error.message}`);
  }

  if (result.status !== 0 && !allowFailure) {
    const detail = result.stderr.toString("utf8").trim();
    fail(detail || `git ${args.join(" ")} failed`);
  }

  return result;
}

function toGitPath(value) {
  return value.split(path.sep).join("/");
}

function shouldSkip(gitPath) {
  const segments = gitPath.split("/");

  if (segments.includes(".git") || segments.includes("node_modules")) {
    return true;
  }

  // Third-party text that must stay verbatim: license/notice aggregations are
  // legally required to preserve upstream contact lines, and vendored trees
  // (v86-master) are upstream code we do not author.
  const base = segments[segments.length - 1].toLowerCase();
  if (base.startsWith("third_party_licenses") || base === "notice" || base.startsWith("notice.")) {
    return true;
  }
  if (segments.includes("v86-master")) {
    return true;
  }

  // Root-level versions/ is the content-addressed snapshot archive convention
  // (rapp-god): filenames are hashes of frozen historical content — immutable
  // history, same class as frames/.
  if (segments[0] === "versions") {
    return true;
  }

  return segments.includes("frames") && gitPath.toLowerCase().endsWith(".json");
}

async function readTrackedText(filePath) {
  let stats;

  try {
    stats = await lstat(filePath);
  } catch (error) {
    if (error.code === "ENOENT") {
      return null;
    }
    throw error;
  }

  let contents;
  if (stats.isSymbolicLink()) {
    contents = Buffer.from(await readlink(filePath), "utf8");
  } else if (stats.isFile()) {
    contents = await readFile(filePath);
  } else {
    return null;
  }

  if (contents.includes(0)) {
    return null;
  }

  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(contents);
  } catch {
    return null;
  }

  for (const character of text) {
    const code = character.codePointAt(0);
    if (code < 32 && code !== 9 && code !== 10 && code !== 12 && code !== 13) {
      return null;
    }
  }

  return text;
}

// A conformant §9 rapp/1-egg is a verified frozen artifact (byte-reproducible,
// manifest-first). Its payload is a recording — linting inside it is linting
// history, so it gets the same skip as frames/. The manifest-first ordering
// guarantees the schema field appears near the start of the document.
function isFrozenEgg(text) {
  // Canonical (sorted-key) eggs put schema near the end; pretty ones near the start.
  const head = text.slice(0, 256);
  const tail = text.slice(-256);
  return (
    head.includes('"schema": "rapp/1-egg"') ||
    head.includes('"schema":"rapp/1-egg"') ||
    tail.includes('"schema": "rapp/1-egg"') ||
    tail.includes('"schema":"rapp/1-egg"')
  );
}

function addLineFindings(findings, gitPath, text) {
  if (isFrozenEgg(text)) {
    return;
  }

  const lines = text.split(/\r?\n/);

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const lineNumber = index + 1;

    if (
      oldRappidPattern.test(line) &&
      mintTeachPattern.test(line) &&
      !legacyMarkerPattern.test(line)
    ) {
      findings.push({
        file: gitPath,
        line: lineNumber,
        rule: "R1",
        message:
          "versioned rappid minting/teaching language lacks a legacy, read-forever, or canonicalized marker",
      });
    }

    if (obsoletePlatformPattern.test(line)) {
      findings.push({
        file: gitPath,
        line: lineNumber,
        rule: "R2",
        message: "obsolete platform expansion; use Prototype Platform",
      });
    }

    if (workAccountPattern.test(line)) {
      findings.push({
        file: gitPath,
        line: lineNumber,
        rule: "R4",
        message: "work-account identifier",
      });
    }

    // Deliberate public business contact — the WildHaven front-door mailbox
    // published on RappterNest. A front door is not a leak.
    const lineWithoutPublicContacts = line.replaceAll(
      ["wildhavenhomesllc", "@gmail.com"].join(""),
      "",
    );

    if (blockedEmailPattern.test(lineWithoutPublicContacts)) {
      findings.push({
        file: gitPath,
        line: lineNumber,
        rule: "R4",
        message: "blocked personal/work email address",
      });
    }
  }
}

function resolveDiffBase(repoRoot) {
  const configuredBase = process.env.GITHUB_BASE?.trim();
  const candidates = configuredBase ? [configuredBase] : ["HEAD~1"];

  for (const candidate of candidates) {
    if (/^0+$/.test(candidate)) {
      continue;
    }

    const result = runGit(
      repoRoot,
      ["rev-parse", "--verify", "--quiet", `${candidate}^{commit}`],
      { allowFailure: true },
    );

    if (result.status === 0) {
      return candidate;
    }
  }

  return null;
}

function changedPaths(repoRoot) {
  const base = resolveDiffBase(repoRoot);
  if (!base) {
    return new Set();
  }

  const result = runGit(repoRoot, [
    "diff",
    "--name-only",
    "-z",
    "--diff-filter=ACMRTUXB",
    `${base}...HEAD`,
  ]);

  return new Set(
    result.stdout
      .toString("utf8")
      .split("\0")
      .filter(Boolean),
  );
}

function addTwinFindings(findings, trackedPaths, changed) {
  const tracked = new Set(trackedPaths);

  for (const jsonPath of trackedPaths) {
    if (path.posix.basename(jsonPath) !== "ecosystem-spec.json") {
      continue;
    }

    const markdownPath = path.posix.join(
      path.posix.dirname(jsonPath),
      "ECOSYSTEM_SPEC.md",
    );
    if (!tracked.has(markdownPath)) {
      continue;
    }

    const jsonChanged = changed.has(jsonPath);
    const markdownChanged = changed.has(markdownPath);
    if (jsonChanged === markdownChanged) {
      continue;
    }

    const changedTwin = jsonChanged ? jsonPath : markdownPath;
    const unchangedTwin = jsonChanged ? markdownPath : jsonPath;
    findings.push({
      file: changedTwin,
      line: 1,
      rule: "R3",
      message: `ecosystem spec twin-pin mismatch; ${unchangedTwin} did not change in the same diff`,
    });
  }
}

if (Number.parseInt(process.versions.node.split(".")[0], 10) < minimumNodeMajor) {
  fail(`Node ${minimumNodeMajor} or newer is required`);
}

const targetDirectory = parseArguments(process.argv.slice(2));
let targetStats;
try {
  targetStats = await lstat(targetDirectory);
} catch (error) {
  fail(`cannot access ${targetDirectory}: ${error.message}`);
}
if (!targetStats.isDirectory()) {
  fail(`--path must name a directory: ${targetDirectory}`);
}

const rootResult = runGit(targetDirectory, ["rev-parse", "--show-toplevel"]);
const repoRoot = rootResult.stdout.toString("utf8").trim();
const targetRelative = toGitPath(path.relative(repoRoot, targetDirectory));
if (targetRelative === ".." || targetRelative.startsWith("../")) {
  fail(`path is outside its Git worktree: ${targetDirectory}`);
}

const pathspec = targetRelative || ".";
const trackedResult = runGit(repoRoot, ["ls-files", "-z", "--", pathspec]);
const trackedPaths = trackedResult.stdout
  .toString("utf8")
  .split("\0")
  .filter(Boolean)
  .filter((gitPath) => !shouldSkip(gitPath))
  .sort();

const findings = [];
let textFileCount = 0;

for (const gitPath of trackedPaths) {
  const text = await readTrackedText(path.join(repoRoot, ...gitPath.split("/")));
  if (text === null) {
    continue;
  }

  textFileCount += 1;
  addLineFindings(findings, gitPath, text);
}

addTwinFindings(findings, trackedPaths, changedPaths(repoRoot));
findings.sort(
  (left, right) =>
    left.file.localeCompare(right.file) ||
    left.line - right.line ||
    left.rule.localeCompare(right.rule),
);

if (findings.length > 0) {
  for (const finding of findings) {
    console.error(
      `${finding.file}:${finding.line}: ${finding.rule} ${finding.message}`,
    );
  }
  console.error(
    `drift-lint: ${findings.length} violation${findings.length === 1 ? "" : "s"}`,
  );
  process.exit(1);
}

console.log(
  `drift-lint: clean (${textFileCount} tracked text file${textFileCount === 1 ? "" : "s"} scanned)`,
);
