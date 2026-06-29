import { readFileSync, writeFileSync } from "node:fs";

const inputPath = "assets/audio/narration.vtt";
const outputPath = "data/captions.js";
const maxChars = 22;

function parseTime(value) {
  const match = value.match(/^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/);
  if (!match) throw new Error(`Invalid VTT timestamp: ${value}`);
  const [, hours, minutes, seconds, millis] = match;
  return Number(hours) * 3600 + Number(minutes) * 60 + Number(seconds) + Number(millis) / 1000;
}

function splitText(text) {
  const clean = text
    .replace(/[。！？；：]+$/u, "")
    .replace(/\s+/g, " ")
    .trim();

  if (clean.length <= maxChars) return [clean];

  const pieces = [];
  let buffer = "";
  for (const part of clean.split(/([，、。！？；：])/u)) {
    if (!part) continue;
    if (/^[，、。！？；：]$/u.test(part)) {
      buffer += part;
      continue;
    }
    if (buffer.length + part.length > maxChars && buffer) {
      pieces.push(buffer.replace(/[，、。！？；：]+$/u, ""));
      buffer = part;
    } else {
      buffer += part;
    }
  }
  if (buffer) pieces.push(buffer.replace(/[，、。！？；：]+$/u, ""));

  return pieces.flatMap((piece) => {
    if (piece.length <= maxChars) return [piece];
    const chunks = [];
    for (let i = 0; i < piece.length; i += maxChars) {
      chunks.push(piece.slice(i, i + maxChars));
    }
    return chunks;
  });
}

const blocks = readFileSync(inputPath, "utf8")
  .trim()
  .split(/\n\s*\n/u)
  .filter((block) => block.includes("-->"));

const captions = [];

for (const block of blocks) {
  const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
  const timeLine = lines.find((line) => line.includes("-->"));
  const text = lines.slice(lines.indexOf(timeLine) + 1).join(" ");
  const [startRaw, endRaw] = timeLine.split(/\s+-->\s+/u);
  const start = parseTime(startRaw);
  const end = parseTime(endRaw);
  const parts = splitText(text);
  const span = end - start;
  const step = span / parts.length;

  for (let i = 0; i < parts.length; i += 1) {
    const previous = captions.at(-1);
    const captionStart = Number((start + step * i).toFixed(2));
    const safeStart = previous ? Math.max(captionStart, Number((previous.end + 0.02).toFixed(2))) : captionStart;
    const safeEnd = Math.max(Number((end - 0.01).toFixed(2)), Number((safeStart + 0.24).toFixed(2)));

    captions.push({
      start: safeStart,
      end: i === parts.length - 1 ? safeEnd : Number((start + step * (i + 1)).toFixed(2)),
      text: parts[i]
    });
  }
}

const body = captions
  .map((caption) => `  { start: ${caption.start}, end: ${caption.end}, text: ${JSON.stringify(caption.text)} }`)
  .join(",\n");

writeFileSync(outputPath, `export const captions = [\n${body}\n];\n`);

console.log(`Generated ${captions.length} captions from ${inputPath}.`);
