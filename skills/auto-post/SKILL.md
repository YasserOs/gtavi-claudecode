---
name: auto-post
description: Run the full Vice Replay routine unattended: pick a live English-language GTA 6 streamer, record, cut a reaction clip, check it, and post it to TikTok, Instagram and YouTube with credit and @tag. Use when the user says "auto post", "run the routine" or schedules clips.
---

# Auto-post (Vice Replay)

Target: 2 to 3 clips per day. The owner chose no per-post approval. Everything below still applies, and any failed gate means skip the clip, never post it.

## Each run

1. **Streamer.** `python scripts/streams.py --query "gta 6"`. Take English-language streamers with 10k+ viewers. Skip anyone posted in the last 12 hours (check `log.md`) and anyone in `takedowns.md`.
2. **Record.** `python scripts/live.py https://twitch.tv/<login> --minutes 8 --ratio 2.5`. No spike means try the next streamer.
3. **Cut.** Put `/opt/homebrew/opt/ffmpeg-full/bin` first on PATH (the default Homebrew ffmpeg has no libass). Run `moments.py` on the spike, extract 3 frames and look at them: GTA 6 on screen, webcam as a separate box. If not, skip. Then `cut.py --layout react --cam auto --title ... --title-style box`.
4. **Title and commentary.** Describe only what is visible or audible. No invented quotes, no spoilers in launch week, no slurs or leaks. Use `hook-writer`.
5. **Gate.** `python scripts/check.py <clip>` must PASS. Re-encode a copy under 10 MB for the browser upload tool: `ffmpeg -i clip.mp4 -c:v libx264 -b:v 1900k -maxrate 2400k -bufsize 4800k -c:a aac -b:a 128k -movflags +faststart clip_upload.mp4`.
6. **Credit (every platform, in the caption, never on the video).** `🎥 Credit: @<streamer>` as a real mention (pick the verified account from the suggestion list), their Twitch name, "Clipped from his live stream. Want it removed? Message us." Max 4 hashtags on Instagram.
7. **Post.**
   - TikTok: `tiktok.com/tiktokstudio/upload`, upload with `file_upload` on the hidden input, cancel the "automatic content checks" popup, type caption, pick the mention, press Post. Confirm the Posts list shows it.
   - Instagram: `instagram.com`, Create (+), upload, click OK on the Reels notice, set crop to **9:16** (default is square and cuts the face), Next, Next, caption, pick the verified mention, Share, wait for "Your reel has been shared".
   - YouTube: `python scripts/youtube_upload.py <clip_upload.mp4> --title ... --description-file ... --privacy public`. Until the API project is audited uploads stay private; then use Chrome at `studio.youtube.com` instead.
8. **Log.** Append to `log.md` and `scoreboard.csv`: time, platform, streamer, title, links.

## Stop conditions

- Any takedown or removal request: remove the clip on all platforms, add the streamer to `takedowns.md`, stop clipping them.
- Not signed in on a platform, a CAPTCHA, a login or verification prompt, or any warning from a platform about the account: stop and tell the owner. Never enter passwords or codes.
- Two failed runs in a row: stop and report.
- Never post leaks, "play early", piracy, or anything that fails `check.py`.
