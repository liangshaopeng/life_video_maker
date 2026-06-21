import json, sys, time
from faster_whisper import WhisperModel

MODEL = sys.argv[1] if len(sys.argv) > 1 else "large-v3"
print(f"Loading model {MODEL}...", flush=True)
t0 = time.time()
model = WhisperModel(MODEL, device="cpu", compute_type="int8")
print(f"Model loaded in {time.time()-t0:.1f}s", flush=True)

segments, info = model.transcribe(
    "source/audio16k.wav",
    language="en",
    beam_size=5,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=400),
)
print(f"Detected language: {info.language} (p={info.language_probability:.2f})", flush=True)

out = []
for seg in segments:
    out.append({
        "id": seg.id,
        "start": round(seg.start, 3),
        "end": round(seg.end, 3),
        "text": seg.text.strip(),
    })
    print(f"[{seg.start:7.2f} -> {seg.end:7.2f}] {seg.text.strip()}", flush=True)

with open("build/transcript_en.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\nDONE: {len(out)} segments -> build/transcript_en.json in {time.time()-t0:.1f}s", flush=True)
