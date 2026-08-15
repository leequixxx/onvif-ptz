<img src="icon.svg" width="96" align="right" alt="">

# ONVIF PTZ for Home Assistant

Point a camera by dragging a joystick, on a dashboard or a phone — plus the
entities and services behind it.

[![hacs][hacs-badge]][hacs-url]
[![release][release-badge]][release-url]
[![license][license-badge]](LICENSE)

[![Open your Home Assistant instance and open this repository inside HACS.][my-badge]][my-url]

[Русская версия](README.ru.md)

<p align="center">
  <img src="docs/demo.gif" alt="Dragging the joystick over live video, then collapsing back to the card" width="720">
</p>

<p align="center">
  <em>Tap the video to fill the screen — the joystick shrinks and floats over it.</em>
</p>

## Why this exists alongside the core ONVIF integration

Home Assistant ships an excellent ONVIF integration, and for most cameras it is
the right choice — it does video, events, sensors and PTZ. This project does not
replace it. It solves two problems that fall outside its scope.

**There is no joystick.** Core exposes the `onvif.ptz` service, and the interface
is left to the user: arrow buttons wired up in YAML, one tap per nudge. That is
fine for occasional corrections and poor for actually aiming a camera. Here the
control surface *is* the feature — a drag-anywhere pad with a dead zone, speed
control and a keep-alive loop, on a card that expands over live video so you can
see what you are pointing at.

**Some cameras never finish ONVIF setup.** Firmware that cannot reach its vendor
cloud often returns a hollow `VideoEncoderConfiguration` — `Encoding: None`,
`Resolution: None` — and core's setup fails with
`There were no H.264 streams available`, taking PTZ down with a media problem.
This integration never touches media profiles, so movement keeps working on
cameras that core cannot configure at all. Add the video separately through
Generic Camera or go2rtc.

Two smaller differences follow from the same design:

- **Clock drift is compensated per request.** Cameras with no RTC battery drift
  by minutes a week and start rejecting WS-Security timestamps. Every request is
  stamped in the camera's own time, so no NTP and no nightly clock script.
- **The card ships inside the integration.** One HACS repository, no Lovelace
  resource to register by hand.

If your camera works with the core integration, use the core integration.

## What's inside

| Path | Purpose |
|---|---|
| `custom_components/onvif_ptz/` | Integration: device, entities, services |
| `custom_components/onvif_ptz/frontend/` | Lovelace card, registered automatically |
| `custom_components/onvif_ptz/brand/` | Integration icon |
| `tools/onvif-check.sh` | Camera diagnostics over curl |
| `tools/check_imaging.py` | The same in Python, with verbose output |
| `icon.svg` | Icon source |

Video is not included — add it separately through **Generic Camera** or go2rtc.
The split is deliberate: PTZ and video break for different reasons, and they
are easier to fix apart.

## Clock drift compensation

ONVIF uses WS-Security with a timestamp, and the camera rejects requests whose
timestamp differs from its own clock by more than a few minutes. That produces
the `Wsse authorized time check failed` error.

The integration calls `GetSystemDateAndTime` — a method the specification
exempts from authentication — works out the offset, and stamps every request
**in the camera's own time**. The offset is recalculated every 10 minutes.

What this means in practice: the camera needs no NTP, no working sync mode and
no nightly script to set its clock. Let it drift by an hour; requests still go
through.

## Installation

### Through HACS

Click the badge above, or add it by hand:

1. HACS → Integrations → three dots → **Custom repositories**
2. Repository URL, category **Integration**
3. Find "ONVIF PTZ", install, restart Home Assistant
4. **Settings → Devices & services → Add integration → ONVIF PTZ**

The card does not need a separate install: it ships inside the integration and
registers itself. No Lovelace resource to add — that step is where most of the
caching trouble comes from.

### Manually

Copy `custom_components/onvif_ptz` into `/config/custom_components/` and restart
Home Assistant.

## Configuring the card

Through the UI: on a dashboard → **Add card** → "ONVIF PTZ". Every option is in
the visual editor; editing YAML is optional.

Minimal YAML:

```yaml
type: custom:onvif-ptz-card
title: Driveway
go2rtc_url: https://…/api/hassio_ingress/…
stream: profile000
speed: 0.6
```

| Option | Purpose |
|---|---|
| `go2rtc_url` | go2rtc address without `/stream.html` |
| `stream` | source name from `go2rtc.yaml` |
| `mode` | `webrtc` (default), `mse` or `mp4` |
| `camera_entity` | fallback through a HA entity when go2rtc is absent |
| `live` | `false` — still frame instead of a stream |
| `speed` | default speed, 0.1–1.0 |
| `axis_lock` | `false` — allow diagonal movement |
| `motion_entity` | motion indicator over the video |
| `night_entity`, `autofocus_entity` | toggle chips |
| `presets` | list of `{name, token}` |

### Video: WebRTC straight from go2rtc

The preferred mode. The card embeds go2rtc's own player, bypassing the HA
`stream` component and HLS entirely.

Home Assistant serves streams over HLS, which costs 3–8 seconds of latency: you
push the joystick, the picture stands still, you push further and overshoot.
WebRTC brings that down to a fraction of a second. HLS repackaging also tends to
break on the very first segment — a stream that dies after three seconds is the
signature — and going direct skips that step.

**Limitation.** If Home Assistant is served over HTTPS while go2rtc is on HTTP,
the browser blocks the content as mixed content. The card says so explicitly.
Options: use the add-on's ingress path, put go2rtc behind the same reverse
proxy, or fall back to the entity route.

### Video through a HA entity

Without `go2rtc_url` the card builds a standard `picture-entity` with
`camera_view: live` — the same path regular HA cards take.

```yaml
camera_entity: camera.yard
live: true
```

Any other stream card can be substituted:

```yaml
stream_card:
  type: custom:webrtc-camera
  url: yard
```

Example go2rtc config:

```yaml
# go2rtc.yaml
streams:
  yard: rtsp://admin:PASSWORD@192.168.2.2:554/cam/realmonitor?channel=1&subtype=1
```

## Icon

It lives in `custom_components/onvif_ptz/brand/` and is picked up automatically
— since Home Assistant 2026.3 custom integrations may ship their own images, and
local files take priority over the brands CDN. No PR to `home-assistant/brands`
required.

On versions older than 2026.3 the UI shows the default placeholder. If the icon
matters there, the files in `brand/` suit a brands PR as they are:
`custom_integrations/onvif_ptz/icon.png` and `icon@2x.png`.

The source is `icon.svg` in the repository root. To rebuild:

```sh
pip install cairosvg
python3 -c "
import cairosvg
for size, name in ((256, 'icon.png'), (512, 'icon@2x.png')):
    cairosvg.svg2png(url='icon.svg',
                     write_to=f'custom_components/onvif_ptz/brand/{name}',
                     output_width=size, output_height=size)
"
```

The ring with four markers is the joystick pad from the card. The camera dome
sits off-centre the way the knob leans when you pan. The only warm colour is the
glow of the infrared illuminator in the lens.

## Picture, IR, motion

| Entity | What it does |
|---|---|
| `number` Brightness / Saturation / Contrast / Sharpness | picture settings |
| `switch` "Night mode" | IR cut filter, when the camera exposes it |
| `switch` "Autofocus" | AUTO / MANUAL focus mode, when supported |
| `binary_sensor` "Motion" | detection over PullPoint |

Only what the camera confirms through `GetOptions` is created. The spread is
wide: plenty of firmware exposes just the four numeric settings and supports
neither the IR filter nor autofocus, in which case no switches appear. Check
your own camera with `onvif-check.sh`.

`SetImagingSettings` replaces the settings wholesale rather than patching them,
so the integration reads the current values before writing. Otherwise adjusting
brightness would zero out contrast.

**About IR logic.** In ONVIF this is `IrCutFilter`, and it reads backwards:
`ON` means the cut filter is in place — daytime colour. `OFF` lets infrared
through and enables night vision. The switch is called "Night mode" and does the
translation itself: on means `IrCutFilter: OFF`. The raw value stays visible in
the `ir_cut_filter` attribute.

**About motion.** A PullPoint subscription is used: the request hangs for up to
30 seconds and returns either with an event or empty. That is cheaper than
frequent polling and gives sub-second latency. The subscription is recreated on
every drop — cheap firmware loses it at the slightest network hiccup.

Some cameras send only the start of an event and never the matching "motion
ended". The sensor therefore clears itself after 30 seconds of silence.

To surface all of this in the card, name the entities:

```yaml
type: custom:onvif-ptz-card
go2rtc_url: https://…/api/hassio_ingress/…
stream: profile000
night_entity: switch.ptz_camera_night_mode
autofocus_entity: switch.ptz_camera_autofocus
motion_entity: binary_sensor.ptz_camera_motion
```

The IR and focus chips stay available in both layouts, including expanded. The
motion indicator appears over the video.

## What shows up in Overview automatically

The integration creates five buttons — left, right, up, down, stop. They land in
the auto-generated Overview on their own, grouped under the device, with no YAML
and no need to take the dashboard over.

The joystick cannot be added that way: Overview is built by the
`original-states` strategy, which only knows about entities and built-in card
types. Custom cards are available only on a dashboard you have taken control of.

## Layout

By default the card adapts to the width of **its own container** rather than the
window — which matters when it sits in a narrow column on a wide monitor.
Container queries are used:

| Card width | Layout |
|---|---|
| under 320 px | tighter padding and labels |
| 320–620 px | video on top, joystick below |
| 620 px and up | video and controls side by side |

The joystick scales with the card (`clamp(150px, 55cqw, 210px)`) and the knob is
repositioned through a `ResizeObserver`.

<img src="docs/card.png" alt="Stacked layout in a narrow column" width="280" align="right">

Two options override the automatic choice:

```yaml
layout: side     # auto (default) | stack | side
align: right     # left | center | right
```

- `auto` switches by card width, as in the table above
- `stack` keeps the joystick below the video at any width
- `side` puts them next to each other at any width

`align` places the joystick when stacked. In the side-by-side layout it also
decides which side the control panel sits on — `left` moves it to the left of the
video, `right` and `center` keep it on the right.

## Expanded mode

<img src="docs/expanded.png" alt="Expanded mode" width="720">

Tapping the video fills the screen with it; the joystick shrinks and floats over
the picture in the bottom-right corner, with `env(safe-area-inset-*)` respected.
Collapse with the corner button or **Escape**.

The tap is caught by a transparent layer over the player: an iframe swallows
pointer events and never forwards them.

Expanding does **not** reload the video — only CSS classes change, and the player
node stays where it is in the tree. Moving the iframe to a different parent would
force the stream to reconnect.

## Control

- **Mouse or finger** — drag the knob out from the centre, release to stop.
- **Keyboard** — focus the joystick (Tab) and hold the arrow keys.
- **Speed** — the slider below, a multiplier for the movement vector.

There is a dead zone (12% of the radius) and a threshold on vector change, so the
camera is not flooded with commands on every mouse twitch. While the knob is off
centre the command repeats every 2 seconds, otherwise the camera stops by its own
`DefaultPTZTimeout`.

**Axis lock** is on by default. Some firmware — Dahua and its clones among them —
honours only the horizontal component when `ContinuousMove` carries both `x` and
`y`, silently dropping the tilt. It looks as though the joystick cannot move up
or down while the arrow buttons work fine. Set `axis_lock: false` on cameras that
handle diagonals.

## Services

| Service | Description |
|---|---|
| `onvif_ptz.move` | Move at `pan` / `tilt` / `zoom` speed (−1…1) |
| `onvif_ptz.stop` | Stop |
| `onvif_ptz.step` | Nudge for `duration` seconds, then stop |
| `onvif_ptz.goto_preset` | Go to a stored position |
| `onvif_ptz.set_preset` | Store the current position |

A dashboard button without the joystick:

```yaml
type: button
name: Left
tap_action:
  action: call-service
  service: onvif_ptz.step
  data:
    pan: -0.6
    duration: 0.5
```

## Languages

English and Russian. Entity and service names come from
`custom_components/onvif_ptz/translations/`; the card picks its language from
`hass.language`, falling back to the browser locale before Home Assistant is
available. Anything else falls back to English.

To add a language: copy `translations/en.json` to `translations/<code>.json`, and
add a matching block to `STRINGS` in
`custom_components/onvif_ptz/frontend/onvif-ptz-card.js`.

## When it will not connect

**`cannot_connect`** — check the port: Dahua and its clones often serve ONVIF on
`8000` rather than `80`. Verify with:

```sh
curl -s -m 5 -X POST http://CAMERA/onvif/device_service \
  -H 'Content-Type: application/soap+xml' \
  -d '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><GetSystemDateAndTime xmlns="http://www.onvif.org/ver10/device/wsdl"/></s:Body></s:Envelope>'
```

A reply containing `UTCDateTime` means the port is right.

**`invalid_auth`** — the credentials were refused. Note that some cameras keep a
separate ONVIF user, created in their user settings.

**Camera in an isolated firewall zone** — forwarding is needed for TCP/80, or
whichever port ONVIF listens on, from the Home Assistant host. If the camera only
answers neighbours on its own subnet, add SNAT on the router: rewrite the source
address to the router's address in that subnet.

## Diagnostics

```sh
sh tools/onvif-check.sh 192.168.2.2 80 admin PASSWORD
```

Needs only `curl` and `openssl`. The WSSE digest is computed against the camera's
clock, so drift does not interfere. The script reports which services answer,
what `GetOptions` allows, and whether motion events arrive.

## Limitations

- Pan, tilt and zoom only. No video and no recording here.
- No absolute positioning — continuous movement and stored positions only.
- Presets are edited as YAML inside the visual editor.

[hacs-badge]: https://img.shields.io/badge/HACS-custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/leequixxx/onvif-ptz
[release-url]: https://github.com/leequixxx/onvif-ptz/releases
[license-badge]: https://img.shields.io/github/license/leequixxx/onvif-ptz
[my-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[my-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=leequixxx&repository=onvif-ptz&category=integration
