---
name: android-reverse-tethering
description: Set up, start, stop, and troubleshoot Android reverse tethering — the phone uses the PC's internet over a USB cable — using gnirehtet and adb. Use when the user wants to share the computer's internet connection with an Android phone over USB, mentions reverse tethering or gnirehtet, or wants the phone online without Wi-Fi or cellular data. Also use when asked whether this works on iPhone.
---

# Android Reverse Tethering (gnirehtet)

Make an Android phone use the PC's internet connection through a USB cable.
Uses [gnirehtet](https://github.com/Genymobile/gnirehtet) (by Genymobile, the
scrcpy authors): a relay server runs on the PC, and a client app on the phone
creates a VPN that routes all phone traffic through USB to the PC's network.
No root required.

## Prerequisites

- Android phone connected via USB with **USB debugging** enabled
  (Settings → Developer options → USB debugging; if Developer options is
  hidden, tap "Build number" 7 times).
- `adb` and `gnirehtet` installed on the PC:
  - **macOS**: `brew install --cask android-platform-tools` and `brew install gnirehtet`
  - **Windows/Linux**: download `adb` (Android platform-tools) and the gnirehtet
    zip from the [gnirehtet releases page](https://github.com/Genymobile/gnirehtet/releases),
    extract, and run the `gnirehtet` binary from the extracted directory.

If a tool is missing, install it first (or guide the user through installing it).

## Start reverse tethering

1. Verify the device is visible and authorized:

   ```sh
   adb devices
   ```

   - Status `device` → ready, continue.
   - Status `unauthorized` → tell the user to accept the "Allow USB debugging"
     prompt on the phone, then re-check.
   - No device listed → tell the user to check the USB cable and that USB
     debugging is enabled, then re-check.

2. Start the relay **as a background/long-running process** (it keeps running
   while tethering is active):

   ```sh
   gnirehtet run
   ```

   On first use this automatically installs the gnirehtet client APK on the
   phone (`Performing Streamed Install` / `Success` in the output) and the
   phone shows a **VPN connection request popup once** — tell the user to
   approve it. On later runs the client connects immediately with no
   interaction needed.

3. Verify from the relay log that it works. Success looks like:

   ```
   INFO TunnelServer: Client #0 connected
   INFO TcpConnection: 10.0.0.2:... -> ...:443 Open
   INFO UdpConnection: 10.0.0.2:... -> 8.8.8.8:53 Open
   ```

   `Client #0 connected` plus TCP/UDP connections opening from `10.0.0.2`
   (the phone's VPN address) means traffic is flowing. A key/lock VPN icon
   appears in the phone's status bar.

4. Tell the user to confirm with the phone's **browser or an app** — NOT
   ping: gnirehtet forwards TCP and UDP only, ICMP does not go through, so
   ping always fails even when tethering works. Wi-Fi and mobile data can be
   turned off; internet keeps working over USB.

## Stop reverse tethering

Stopping has **two steps — doing only the first one breaks the phone's
internet** (the VPN stays up on the phone with nowhere to send traffic):

1. Terminate the `gnirehtet run` relay process (Ctrl+C or kill the background
   process).
2. Bring down the VPN on the phone:

   ```sh
   gnirehtet stop
   ```

Verify no relay process remains (e.g. `pgrep -fl gnirehtet` on macOS/Linux).
The client app stays installed on the phone; restarting later only takes
`gnirehtet run` again.

Alternative: the user can also disconnect from the phone itself via the VPN
notification in the status bar.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `adb: command not found` | Install platform-tools (see Prerequisites). |
| Device `unauthorized` | Accept the USB debugging prompt on the phone. |
| Device not listed | Check cable/port; enable USB debugging; some cables are charge-only. |
| Phone has no internet after stopping | The relay was killed without `gnirehtet stop` — run `gnirehtet stop`, or disable the VPN from the phone's status bar. |
| Ping fails but browser works | Expected — ICMP is not forwarded. Only TCP/UDP work. |
| USB unplugged | Tethering drops. Re-plug and run `gnirehtet run` again. |

## Notes and caveats

- **iPhone is not supported.** gnirehtet depends on adb and Android's VPN
  API. iOS has no supported USB reverse-tethering path on non-jailbroken
  devices. Alternative for iPhone users on a Mac: Internet Sharing
  (System Settings → General → Sharing → Internet Sharing) to create a Wi-Fi
  hotspot — this requires the Mac itself to be on a wired (Ethernet)
  connection so its Wi-Fi is free to share.
- The phone's traffic exits through the PC's network. On a corporate
  machine/network, remind the user to check their organization's security
  policy before using this.
- The relay listens on local port 31416 by default.
