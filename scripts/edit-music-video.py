#!/usr/bin/env python3
"""
Beat-synced music video editor.

Takes a stitched video of transitions, an audio file, and a section map,
then creates a music video where clips are synced to song sections with
energy-based speed ramping and professional transitions.

Usage:
    python3 edit-music-video.py \
        --video raw-video.mp4 \
        --audio song.mp3 \
        --sections sections.json \
        --output final.mp4

Section map JSON format:
{
    "sections": [
        {
            "clip_index": 0,
            "song_start": 0.0,
            "song_end": 17.0,
            "transition": "none",
            "description": "Intro"
        },
        ...
    ],
    "clip_duration": 8.0,
    "effects": {
        "vignette_clips": [6],
        "energy_influence": 0.6,
        "min_speed_mult": 0.5,
        "max_speed_mult": 2.0
    }
}
"""

import argparse
import json
import os
import sys
import subprocess
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Beat-synced music video editor")
    parser.add_argument("--video", required=True, help="Source video (stitched transitions)")
    parser.add_argument("--audio", required=True, help="Audio file (MP3)")
    parser.add_argument("--sections", required=True, help="Section map JSON")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--fps", type=int, default=24, help="Output FPS (default: 24)")
    args = parser.parse_args()

    # Check dependencies
    try:
        import librosa
        from scipy.ndimage import gaussian_filter1d
    except ImportError:
        print("Installing dependencies...", file=sys.stderr)
        os.system("pip3 install librosa scipy soundfile -q")
        import librosa
        from scipy.ndimage import gaussian_filter1d

    # Load section map
    with open(args.sections) as f:
        config = json.load(f)

    sections = config["sections"]
    clip_duration = config.get("clip_duration", 8.0)
    effects = config.get("effects", {})
    energy_influence = effects.get("energy_influence", 0.6)
    min_speed_mult = effects.get("min_speed_mult", 0.5)
    max_speed_mult = effects.get("max_speed_mult", 2.0)
    vignette_clips = set(effects.get("vignette_clips", []))

    # Transition frame counts
    FLASH_FRAMES = 4
    CROSSFADE_FRAMES = 18
    GLITCH_FRAMES = 12

    OUTPUT_FPS = args.fps
    SOURCE_FPS = args.fps

    # === Audio analysis ===
    print("Analyzing audio...")
    y, sr = librosa.load(args.audio, sr=22050)
    song_duration = librosa.get_duration(y=y, sr=sr)

    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    rms_smooth = gaussian_filter1d(rms, sigma=30)
    rms_smooth = rms_smooth / (rms_smooth.max() + 1e-8)

    print(f"  Duration: {song_duration:.1f}s")

    # === Load video ===
    print("Loading video...")
    probe = subprocess.run([
        'ffprobe', '-v', 'quiet', '-show_entries', 'stream=width,height',
        '-select_streams', 'v:0', '-of', 'csv=p=0', args.video
    ], capture_output=True, text=True)
    w, h = map(int, probe.stdout.strip().split(','))

    result = subprocess.run([
        'ffmpeg', '-y', '-v', 'quiet', '-i', args.video,
        '-vf', f'fps={SOURCE_FPS}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'
    ], capture_output=True)
    all_frames = np.frombuffer(result.stdout, dtype=np.uint8).reshape(-1, h, w, 3)
    n_source = len(all_frames)
    print(f"  {n_source} frames ({w}x{h})")

    # === Build time remap ===
    print("Building time remap...")
    total_output = int(song_duration * OUTPUT_FPS)
    output_times = np.arange(total_output) / OUTPUT_FPS
    input_times = np.zeros(total_output)

    for sec in sections:
        ci = sec["clip_index"]
        s_start = sec["song_start"]
        s_end = sec["song_end"]
        sec_dur = s_end - s_start
        c_start = ci * clip_duration
        base_speed = clip_duration / sec_dur

        mask = (output_times >= s_start) & (output_times < s_end)
        indices = np.where(mask)[0]
        if len(indices) == 0:
            continue

        frame_energies = np.interp(output_times[indices], rms_times, rms_smooth)
        e_min, e_max = frame_energies.min(), frame_energies.max()
        if e_max - e_min > 0.02:
            e_norm = (frame_energies - e_min) / (e_max - e_min)
        else:
            e_norm = np.full_like(frame_energies, 0.5)

        speed_mult = min_speed_mult + e_norm * (max_speed_mult - min_speed_mult)
        speed_mult = (1.0 - energy_influence) + energy_influence * speed_mult

        dt = 1.0 / OUTPUT_FPS
        advances = base_speed * speed_mult * dt
        advances *= clip_duration / advances.sum()

        cumulative = np.cumsum(advances)
        cumulative = np.insert(cumulative, 0, 0.0)[:-1]
        input_times[indices] = c_start + np.clip(cumulative, 0, clip_duration - 0.01)

    input_times = gaussian_filter1d(input_times, sigma=1.5)
    n_clips = len(sections)
    input_times = np.clip(input_times, 0, n_clips * clip_duration - 1.0 / SOURCE_FPS)

    source_indices = np.clip((input_times * SOURCE_FPS).astype(int), 0, n_source - 1)

    # === Build transition zones ===
    print("Setting up transitions...")
    transition_zones = {}
    white_frame = np.full((h, w, 3), 255, dtype=np.uint8)

    for si in range(1, len(sections)):
        sec = sections[si]
        prev = sections[si - 1]
        trans = sec.get("transition", "cut")
        center = int(sec["song_start"] * OUTPUT_FPS)

        if trans == "flash":
            half = FLASH_FRAMES // 2
            for off in range(-half, half + 2):
                f = center + off
                if 0 <= f < total_output:
                    intensity = max(0, 1.0 - abs(off) / max(half + 1, 1) * 0.7)
                    transition_zones[f] = ("flash", intensity, si)

        elif trans == "crossfade":
            half = CROSSFADE_FRAMES // 2
            for off in range(-half, half + 1):
                f = center + off
                if 0 <= f < total_output:
                    blend = (off + half) / (2 * half)
                    transition_zones[f] = ("crossfade", blend, si)

        elif trans == "glitch":
            half = GLITCH_FRAMES // 2
            for off in range(-half, half + 1):
                f = center + off
                if 0 <= f < total_output:
                    progress = (off + half) / (2 * half)
                    transition_zones[f] = ("glitch", progress, si)

    # === Precompute vignette mask ===
    vignette_mask = None
    if vignette_clips:
        yy, xx = np.ogrid[:h, :w]
        cy, cx = h / 2, w / 2
        dist = np.sqrt((xx - cx)**2 + (yy - cy)**2)
        max_dist = np.sqrt(cx**2 + cy**2)
        vignette_mask = 1.0 - 0.35 * (dist / max_dist) ** 1.5

    # === Render ===
    print("Rendering...")
    output_data = bytearray()
    prev_pct = -1

    for i in range(total_output):
        base_frame = all_frames[source_indices[i]]

        if i in transition_zones:
            ttype, param, si = transition_zones[i]
            prev_sec = sections[si - 1]
            curr_sec = sections[si]

            if ttype == "flash":
                frame = (base_frame.astype(np.float32) * (1.0 - param * 0.85) +
                         white_frame.astype(np.float32) * param * 0.85).astype(np.uint8)

            elif ttype == "crossfade":
                pci = prev_sec["clip_index"]
                cci = curr_sec["clip_index"]
                out_t = (pci + 1) * clip_duration - 0.2 * (1.0 - param)
                in_t = cci * clip_duration + 0.2 * param
                out_idx = min(max(int(out_t * SOURCE_FPS), 0), n_source - 1)
                in_idx = min(max(int(in_t * SOURCE_FPS), 0), n_source - 1)
                t = param * param * (3 - 2 * param)
                frame = (all_frames[out_idx].astype(np.float32) * (1 - t) +
                         all_frames[in_idx].astype(np.float32) * t).astype(np.uint8)

            elif ttype == "glitch":
                pci = prev_sec["clip_index"]
                cci = curr_sec["clip_index"]
                out_idx = min(max(int((pci + 1) * clip_duration * SOURCE_FPS - 8), 0), n_source - 1)
                in_idx = min(max(int(cci * clip_duration * SOURCE_FPS + 3), 0), n_source - 1)

                frame = base_frame.copy()
                np.random.seed(42 + i)
                n_bands = np.random.randint(4, 8)
                band_starts = sorted(np.random.randint(0, h, n_bands))

                for bi in range(len(band_starts)):
                    y_s = band_starts[bi]
                    y_e = band_starts[bi + 1] if bi + 1 < len(band_starts) else h
                    x_shift = np.random.randint(-40, 40)
                    src = all_frames[in_idx] if (param > 0.5) != (bi % 2 == 0) else all_frames[out_idx]
                    band = src[y_s:y_e].copy()
                    if 0 < abs(x_shift) < w:
                        if x_shift > 0:
                            band[:, x_shift:] = band[:, :-x_shift].copy()
                            band[:, :x_shift] = 0
                        else:
                            band[:, :x_shift] = band[:, -x_shift:].copy()
                            band[:, x_shift:] = 0
                    frame[y_s:y_e] = band

                for sl in range(0, h, 3):
                    frame[sl] = (frame[sl].astype(np.float32) * 0.7).astype(np.uint8)

                shift = max(1, min(int((0.5 - min(param, 0.5)) * 12), w // 4))
                if shift > 0 and shift < w:
                    shifted = frame.copy()
                    shifted[:, shift:, 0] = frame[:, :-shift, 0]
                    shifted[:, :-shift, 2] = frame[:, shift:, 2]
                    frame = shifted

            output_data.extend(frame.tobytes())
        else:
            current_clip = int(input_times[i] / clip_duration)
            if current_clip in vignette_clips and vignette_mask is not None:
                frame = (base_frame.astype(np.float32) * vignette_mask[:, :, np.newaxis]).astype(np.uint8)
                output_data.extend(frame.tobytes())
            else:
                output_data.extend(base_frame.tobytes())

        pct = int((i / total_output) * 100)
        if pct != prev_pct and pct % 5 == 0:
            print(f"  {pct}%", end='\r')
            prev_pct = pct

    print(f"  100% — {total_output} frames")

    # === Encode ===
    print("Encoding...")
    proc = subprocess.Popen([
        'ffmpeg', '-y', '-v', 'warning',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24',
        '-s', f'{w}x{h}', '-r', str(OUTPUT_FPS),
        '-i', 'pipe:0',
        '-i', args.audio,
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
        '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p', '-shortest',
        '-movflags', '+faststart',
        args.output
    ], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = proc.communicate(input=bytes(output_data))

    if proc.returncode == 0:
        size_mb = os.path.getsize(args.output) / (1024 * 1024)
        print(f"\n✓ {args.output} ({size_mb:.0f}MB, {song_duration:.1f}s)")
    else:
        print(f"\n✗ {stderr.decode()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
