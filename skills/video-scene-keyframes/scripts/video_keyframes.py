#!/usr/bin/env python3
"""Save one keyframe per scene (or one frame every N seconds) from direct video file links.

Runs the paid Apify Actor conserving_celerytop/video-scene-keyframes, built by Don Mangu, on the
user's own Apify account. Direct video file links only (MP4, MOV, WebM and similar). Links to
YouTube, TikTok, Instagram and other video platforms are refused by the Actor. Use videos you own
or have the right to process.
Writes <out>_frames.csv (one row per frame, with timecodes and image links) and <out>.md.
With --download-frames it also saves the frame images into <out>/.

Scene mode is charged per started minute; interval mode per frame; reading on-screen text per
frame where text is found. Video above Full HD or 30 fps counts 2 to 8 units per minute.

Run with --estimate first: it prints the cost ceiling from live prices and makes no run.
Needs: pip install apify-client, and APIFY_TOKEN in the environment.
"""
import argparse
import csv
import math
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apify_common as ac  # noqa: E402

ACTOR = "conserving_celerytop/video-scene-keyframes"
COLUMNS = ["videoUrl", "status", "sceneNumber", "frameNumber", "sceneStartTimecode", "sceneEndTimecode",
           "frameTimecode", "frameUrl", "onScreenText", "scenesDetected", "framesSaved", "minutesAnalyzed",
           "billedMinuteUnits", "videoDurationSeconds", "contactSheetUrl", "note", "error"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--urls", default="", help="Comma list of direct video file URLs")
    p.add_argument("--urls-file", default="", help="File with one video URL per line")
    p.add_argument("--mode", choices=["scenes", "interval"], default="scenes", help="One frame per scene, or one every N seconds")
    p.add_argument("--interval-seconds", type=float, default=10, help="Interval mode: seconds between frames (default 10)")
    p.add_argument("--max-frames", type=int, default=50, help="Most frames saved per video (default 50)")
    p.add_argument("--read-text", action="store_true", help="Read on-screen text in each saved frame (OCR, extra charge where text is found)")
    p.add_argument("--ocr-language", default="eng", help="eng, deu, fra, spa, ita, por or nld")
    p.add_argument("--scene-threshold", type=int, default=None, help="Lower finds more scene changes (default 27)")
    p.add_argument("--min-scene-seconds", type=float, default=None, help="Merge scenes shorter than this (default 1)")
    p.add_argument("--frame-width", type=int, default=None, help="Scale frames down to this width in pixels (default 1280)")
    p.add_argument("--max-minutes-per-video", type=int, default=30, help="Only analyse this many minutes from the start (default 30)")
    p.add_argument("--max-videos", type=int, default=100, help="Most videos processed")
    p.add_argument("--video-minutes", type=float, default=None,
                   help="Total minutes of video, for a closer estimate. Default: the per-video maximum for every video")
    p.add_argument("--units-per-minute", type=int, default=1,
                   help="1 for Full HD at 30 fps or smaller. Use 2 to 8 for 1440p, 4K or 60 fps video")
    p.add_argument("--download-frames", action="store_true", help="Also save the frame images to <out>/")
    p.add_argument("--max-charge", type=float, default=None, help="Hard spending cap in USD (default: ceiling plus 25 percent)")
    p.add_argument("--yes", action="store_true", help="The user has seen the estimate and agreed (needed above 1 USD)")
    p.add_argument("--out", default="keyframes", help="Output prefix and folder")
    p.add_argument("--estimate", action="store_true", help="Print the cost ceiling from live prices and stop")
    a = p.parse_args()

    urls = ac.read_entries(a.urls_file, a.urls, limit=500)[: a.max_videos]
    if not urls:
        sys.exit("Give --urls or --urls-file.")
    n = len(urls)
    frames_ceiling = n * a.max_frames
    if a.mode == "scenes":
        minutes = a.video_minutes if a.video_minutes is not None else n * a.max_minutes_per_video
        lines = [(ACTOR, "video-minute", math.ceil(minutes) * a.units_per_minute,
                  f"ceiling, {a.units_per_minute} unit(s) per started minute")]
    else:
        # Interval mode saves at most one frame per interval, and at most --max-frames per video.
        mins = a.video_minutes / n if a.video_minutes is not None else a.max_minutes_per_video
        per_video = min(a.max_frames, math.ceil(min(mins, a.max_minutes_per_video) * 60 / a.interval_seconds))
        frames_ceiling = n * per_video
        lines = [(ACTOR, "frame", frames_ceiling, "ceiling, frames saved")]
    if a.read_text:
        lines.append((ACTOR, "frame-text", frames_ceiling, "ceiling, only frames where text is found"))
    total = ac.estimate(lines)
    if a.estimate:
        return
    ac.require_yes(total, a.yes)

    apify = ac.client()
    cap = ac.resolve_cap(a.max_charge, total)
    run_input = {"videoUrls": urls, "mode": a.mode, "intervalSeconds": a.interval_seconds,
                 "maxFramesPerVideo": a.max_frames, "readOnScreenText": a.read_text, "ocrLanguage": a.ocr_language,
                 "maxMinutesPerVideo": a.max_minutes_per_video, "maxVideos": a.max_videos}
    if a.scene_threshold is not None:
        run_input["sceneThreshold"] = a.scene_threshold
    if a.min_scene_seconds is not None:
        run_input["minSceneSeconds"] = a.min_scene_seconds
    if a.frame_width is not None:
        run_input["frameWidth"] = a.frame_width
    _, rows, _ = ac.run_actor(apify, ACTOR, run_input, cap)

    with open(a.out + "_frames.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if r.get("status") == "ok" and r.get("frameUrl")]
    failed = [r for r in rows if r.get("status") != "ok"]
    if a.download_frames and ok:
        os.makedirs(a.out, exist_ok=True)
        for i, r in enumerate(ok, 1):
            ext = os.path.splitext(r["frameUrl"].split("?")[0])[1] or ".jpg"
            try:
                urllib.request.urlretrieve(r["frameUrl"], os.path.join(a.out, f"{i:04d}{ext}"))
            except OSError as e:
                print(f"  Could not save frame {i}: {e}")
    md = [f"# {len(ok)} frames from {len(urls)} video(s)", ""]
    for r in ok:
        text = f" Text: {r['onScreenText']}" if r.get("onScreenText") else ""
        scene = f"scene {r['sceneNumber']}, " if r.get("sceneNumber") else ""
        md.append(f"- {scene}frame at {r.get('frameTimecode')} ({r.get('videoUrl')}) {r.get('frameUrl')}.{text}")
    if failed:
        md += ["", "## Not processed", ""] + [f"- {r.get('status')}: {r.get('videoUrl')} {r.get('error') or ''}" for r in failed]
    with open(a.out + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"Wrote {len(ok)} frames to {a.out}_frames.csv and {a.out}.md. Not processed: {len(failed)}")


if __name__ == "__main__":
    main()
