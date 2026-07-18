# Video Recording Checklist

## Capture setup

- [ ] Use a browser content area of **1440 x 900 px**.
- [ ] Set browser zoom to **90%** so the summary, timeline, Finding register, and details remain visible together.
- [ ] Use the local application at `http://127.0.0.1:8765/`.
- [ ] Confirm the application header shows `LOCAL · PUBLIC-SAFE`.
- [ ] Hide bookmarks, personal tabs, profile menus, notifications, email, chat, and desktop overlays.
- [ ] Close or hide terminals that contain local usernames or paths.
- [ ] Use only the three built-in synthetic scenarios; do not upload a private file.
- [ ] Record at 1080p or higher with the pointer visible.

## Exact click sequence

Target duration: **2 minutes 30 seconds**, with an absolute maximum below three minutes.

1. Open the application and show **Optional custom input** for two seconds.
2. Leave **Normal recording** selected and click **Run analysis**.
3. Point to `NORMAL`, `100.00%` recording continuity, `100.00%` LiDAR relative availability, and `0` detected findings.
4. Open the **Recording** selector and choose **LiDAR-only 3.4 s stall**.
5. Click **Run analysis**.
6. Point to `3` detected findings, `1 primary incident · 2 related findings`, `100.00%` recording continuity, and approximately `71.67%` LiDAR relative availability.
7. Trace the red finding window across the timeline and show that encoder, IMU, and motor continue through the LiDAR silence.
8. In **Finding register**, select `FND-001` / `LIDAR_STREAM_STALL`.
9. In **Finding details**, open **Evidence**, then **Next tests**.
10. Briefly select `FND-002` or `FND-003` to show the dashed **RELATED** classification.
11. Click **HTML report** in the export package and show that the report downloads.
12. Return to the application, open the **Recording** selector, and choose **Global 3.4 s recording gap**.
13. Click **Run analysis**.
14. Point to `RECORDING-WIDE GAP`, approximately `71.67%` recording continuity, `100.00%` LiDAR relative availability, and one primary finding.
15. Show that all four timeline rows are silent inside the gap.
16. End on the application header and summary, not on a download or personal browser page.

## Narration checkpoints

- [ ] State that the field engineer defined and validated the forensic method.
- [ ] State that Codex converted the method into a clean-room, public-safe product.
- [ ] Explain that the detector distinguishes what stopped from what continued.
- [ ] Explain the different denominators for recording continuity and LiDAR relative availability.
- [ ] State that timing evidence characterizes a failure signature but does not prove firmware, driver, network, power, or hardware root cause.
- [ ] State that all visible demonstration data are deterministic and synthetic.
- [ ] Do not claim that AI independently discovered the physical failure.

## Final privacy check

- [ ] Notifications are disabled.
- [ ] No personal browser tabs or account avatar are visible.
- [ ] No private files, customer names, device identifiers, coordinates, or proprietary software names are visible.
- [ ] No API key, password manager, terminal history, email address, or local user directory is visible.
- [ ] The finished video is under three minutes and reviewed once before upload.
- [ ] Upload and final competition submission remain manual human actions.
