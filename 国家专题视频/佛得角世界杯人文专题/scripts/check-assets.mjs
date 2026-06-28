import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const manifest = JSON.parse(readFileSync("assets/footage/manifest.json", "utf8"));
const errors = [];

for (const asset of manifest.assets) {
  const clipPath = path.join("assets/footage", asset.clipFile);
  if (!existsSync(clipPath)) {
    errors.push(`missing clip ${clipPath}`);
    continue;
  }
  const durationRaw = execFileSync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    clipPath
  ], { encoding: "utf8" }).trim();
  const duration = Number.parseFloat(durationRaw);
  if (!Number.isFinite(duration) || duration < 4) {
    errors.push(`clip ${clipPath} has invalid duration ${durationRaw}`);
    continue;
  }
  if (typeof asset.duration === "number" && duration + 0.25 < asset.duration) {
    errors.push(`clip ${clipPath} is ${duration.toFixed(2)}s, expected at least ${asset.duration}s`);
  }
}

if (errors.length > 0) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Verified ${manifest.assets.length} footage assets.`);
