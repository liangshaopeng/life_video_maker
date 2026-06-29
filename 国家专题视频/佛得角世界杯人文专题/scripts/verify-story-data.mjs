import { captions } from "../data/captions.js";
import { claims, sources } from "../data/sources.js";
import { storyboard, targetDuration } from "../data/storyboard.js";

const errors = [];
const sourceIds = new Set(sources.map((source) => source.id));

if (targetDuration < 180 || targetDuration > 300) {
  errors.push(`targetDuration must be between 180 and 300 seconds, got ${targetDuration}`);
}

for (let i = 0; i < storyboard.length; i += 1) {
  const scene = storyboard[i];
  if (!scene.id || !scene.title) errors.push(`scene ${i} is missing id or title`);
  if (typeof scene.start !== "number" || typeof scene.duration !== "number") {
    errors.push(`scene ${scene.id} start and duration must be numbers`);
  }
  if (scene.duration <= 0) errors.push(`scene ${scene.id} has non-positive duration`);
  if (!scene.narration || scene.narration.length < 20) {
    errors.push(`scene ${scene.id} narration is too short`);
  }
  if (i > 0 && scene.start !== storyboard[i - 1].start + storyboard[i - 1].duration) {
    errors.push(`scene ${scene.id} does not start after previous scene`);
  }
}

const computedDuration = storyboard.at(-1).start + storyboard.at(-1).duration;
if (computedDuration !== targetDuration) {
  errors.push(`storyboard duration ${computedDuration} does not equal targetDuration ${targetDuration}`);
}

for (const caption of captions) {
  if (caption.start < 0 || caption.end <= caption.start) {
    errors.push(`caption has invalid timing: ${JSON.stringify(caption)}`);
  }
  if (!caption.text || caption.text.length > 28) {
    errors.push(`caption text must be 1-28 chars: ${JSON.stringify(caption)}`);
  }
  if (caption.end > targetDuration + 0.5) {
    errors.push(`caption exceeds target duration: ${JSON.stringify(caption)}`);
  }
}

for (const claim of claims) {
  for (const sourceId of claim.sourceIds) {
    if (!sourceIds.has(sourceId)) {
      errors.push(`claim ${claim.id} references missing source ${sourceId}`);
    }
  }
}

if (!claims.some((claim) => claim.id === "argentina-opponent")) {
  errors.push("missing current Argentina opponent claim");
}

if (errors.length > 0) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Verified ${storyboard.length} scenes, ${captions.length} captions, ${sources.length} sources.`);
