"""A minimal ONVIF client: only what PTZ needs.

Written on plain aiohttp and ElementTree rather than onvif-zeep, because:
  * no external dependencies, so nothing breaks on a Home Assistant upgrade;
  * media profiles are never touched, so cameras with an incomplete
    VideoEncoderConfiguration (empty Encoding/Resolution) still work;
  * the clock offset is computed here, so WS-Security passes even on
    cameras left at DateTimeType=Manual with a drifted clock.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import aiohttp

_LOGGER = logging.getLogger(__name__)

NS = {
    "s": "http://www.w3.org/2003/05/soap-envelope",
    "tds": "http://www.onvif.org/ver10/device/wsdl",
    "trt": "http://www.onvif.org/ver10/media/wsdl",
    "tptz": "http://www.onvif.org/ver20/ptz/wsdl",
    "timg": "http://www.onvif.org/ver20/imaging/wsdl",
    "tev": "http://www.onvif.org/ver10/events/wsdl",
    "wsa": "http://www.w3.org/2005/08/addressing",
    "wsnt": "http://docs.oasis-open.org/wsn/b-2",
    "tt": "http://www.onvif.org/ver10/schema",
}

CLOCK_REFRESH = timedelta(minutes=10)

ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"'
    ' xmlns:tds="http://www.onvif.org/ver10/device/wsdl"'
    ' xmlns:trt="http://www.onvif.org/ver10/media/wsdl"'
    ' xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"'
    ' xmlns:timg="http://www.onvif.org/ver20/imaging/wsdl"'
    ' xmlns:tev="http://www.onvif.org/ver10/events/wsdl"'
    ' xmlns:wsa="http://www.w3.org/2005/08/addressing"'
    ' xmlns:tt="http://www.onvif.org/ver10/schema">'
    "{header}<s:Body>{body}</s:Body></s:Envelope>"
)

WSSE = (
    "<s:Header><Security s:mustUnderstand=\"1\""
    ' xmlns="http://docs.oasis-open.org/wss/2004/01/'
    'oasis-200401-wss-wssecurity-secext-1.0.xsd">'
    "<UsernameToken><Username>{user}</Username>"
    '<Password Type="http://docs.oasis-open.org/wss/2004/01/'
    'oasis-200401-wss-username-token-profile-1.0#PasswordDigest">'
    "{digest}</Password>"
    '<Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/'
    'oasis-200401-wss-soap-message-security-1.0#Base64Binary">'
    "{nonce}</Nonce>"
    '<Created xmlns="http://docs.oasis-open.org/wss/2004/01/'
    'oasis-200401-wss-wssecurity-utility-1.0.xsd">{created}</Created>'
    "</UsernameToken></Security></s:Header>"
)


class OnvifError(Exception):
    """The camera returned a fault, or did not answer at all."""


class OnvifPtzClient:
    """Pan-tilt control over ONVIF.

    Every public method is a coroutine. The client owns its aiohttp
    session unless one is passed in.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._user = username
        self._password = password
        self._session = session
        self._owns_session = session is None

        self._device_url = f"http://{host}:{port}/onvif/device_service"
        self._media_url: str | None = None
        self._ptz_url: str | None = None
        self._imaging_url: str | None = None
        self._events_url: str | None = None
        self._pullpoint_url: str | None = None

        self._clock_offset = timedelta(0)
        self._clock_checked: datetime | None = None
        self._lock = asyncio.Lock()

        self.profile_token: str | None = None
        self.video_source_token: str | None = None
        self.device_name: str | None = None
        self.serial: str | None = None
        self.has_zoom = False
        self.has_ir = False
        self.has_autofocus = False
        self.has_events = False
        self.imaging_ranges: dict[str, tuple[float, float]] = {}


    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    def _security_header(self) -> str:
        """A WSSE UsernameToken stamped in the CAMERA's time, not ours.

        This is what makes clock drift harmless: the Created timestamp
        always lands inside the acceptance window from the camera's point
        of view.
        """
        nonce = os.urandom(16)
        created = (datetime.now(timezone.utc) + self._clock_offset).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        digest = hashlib.sha1(
            nonce + created.encode("utf-8") + self._password.encode("utf-8")
        ).digest()
        return WSSE.format(
            user=escape(self._user),
            digest=base64.b64encode(digest).decode(),
            nonce=base64.b64encode(nonce).decode(),
            created=created,
        )

    async def _call(
        self, url: str, body: str, *, auth: bool = True, timeout: int = 10
    ) -> ET.Element:
        if auth:
            await self._sync_clock()
            header = self._security_header()
        else:
            header = ""

        payload = ENVELOPE.format(header=header, body=body)
        session = await self._ensure_session()

        try:
            async with session.post(
                url,
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                text = await resp.text()
        except asyncio.TimeoutError as err:
            raise OnvifError(f"Camera {self._host} did not answer within {timeout}s") from err
        except aiohttp.ClientError as err:
            raise OnvifError(f"Connection error to {self._host}: {err}") from err

        try:
            root = ET.fromstring(text)
        except ET.ParseError as err:
            raise OnvifError(f"Camera returned non-XML: {text[:200]}") from err

        fault = root.find(".//s:Fault", NS)
        if fault is not None:
            reason = fault.find(".//s:Text", NS)
            detail = reason.text if reason is not None else "unknown error"
            raise OnvifError(f"SOAP Fault: {detail}")

        return root


    async def _sync_clock(self, force: bool = False) -> None:
        """Recompute the clock offset.

        The specification exempts GetSystemDateAndTime from
        authentication, which is exactly why the camera's time can be
        read before a valid WS-Security header can be built.
        """
        now = datetime.now(timezone.utc)
        if (
            not force
            and self._clock_checked is not None
            and now - self._clock_checked < CLOCK_REFRESH
        ):
            return

        root = await self._call(
            self._device_url, "<tds:GetSystemDateAndTime/>", auth=False
        )
        utc = root.find(".//tt:UTCDateTime", NS)
        if utc is None:
            self._clock_offset = timedelta(0)
            self._clock_checked = now
            return

        def _num(path: str) -> int:
            node = utc.find(path, NS)
            return int(node.text) if node is not None and node.text else 0

        try:
            cam_time = datetime(
                _num("tt:Date/tt:Year"),
                _num("tt:Date/tt:Month"),
                _num("tt:Date/tt:Day"),
                _num("tt:Time/tt:Hour"),
                _num("tt:Time/tt:Minute"),
                _num("tt:Time/tt:Second"),
                tzinfo=timezone.utc,
            )
        except ValueError:
            self._clock_offset = timedelta(0)
            self._clock_checked = now
            return

        self._clock_offset = cam_time - now
        self._clock_checked = now

        drift = abs(self._clock_offset.total_seconds())
        if drift > 60:
            _LOGGER.debug(
                "Clock on %s is off by %.0fs, compensating",
                self._host,
                drift,
            )


    async def async_setup(self) -> None:
        """Discover service addresses and the first PTZ-capable profile."""
        async with self._lock:
            await self._sync_clock(force=True)
            await self._discover_services()
            await self._discover_profile()
            await self._read_device_info()

    async def _discover_services(self) -> None:
        try:
            root = await self._call(
                self._device_url,
                "<tds:GetCapabilities><tds:Category>All</tds:Category>"
                "</tds:GetCapabilities>",
            )
            media = root.find(".//tt:Media/tt:XAddr", NS)
            ptz = root.find(".//tt:PTZ/tt:XAddr", NS)
            imaging = root.find(".//tt:Imaging/tt:XAddr", NS)
            events = root.find(".//tt:Events/tt:XAddr", NS)
            self._media_url = media.text if media is not None else None
            self._ptz_url = ptz.text if ptz is not None else None
            self._imaging_url = imaging.text if imaging is not None else None
            self._events_url = events.text if events is not None else None
        except OnvifError as err:
            _LOGGER.debug("GetCapabilities failed (%s), falling back to default paths", err)

        self._media_url = self._fix_host(self._media_url) or (
            f"http://{self._host}:{self._port}/onvif/media_service"
        )
        self._ptz_url = self._fix_host(self._ptz_url) or (
            f"http://{self._host}:{self._port}/onvif/ptz_service"
        )
        self._imaging_url = self._fix_host(self._imaging_url) or (
            f"http://{self._host}:{self._port}/onvif/imaging_service"
        )
        self._events_url = self._fix_host(self._events_url) or (
            f"http://{self._host}:{self._port}/onvif/event_service"
        )

    def _fix_host(self, url: str | None) -> str | None:
        if not url:
            return None
        try:
            from urllib.parse import urlparse, urlunparse

            parts = urlparse(url)
            if parts.hostname == self._host:
                return url
            return urlunparse(
                parts._replace(netloc=f"{self._host}:{self._port}")
            )
        except ValueError:
            return None

    async def _discover_profile(self) -> None:
        root = await self._call(self._media_url, "<trt:GetProfiles/>")
        tokens = [
            p.get("token")
            for p in root.findall(".//trt:Profiles", NS)
            if p.get("token")
        ]
        if not tokens:
            raise OnvifError("The camera returned no profiles")

        for prof in root.findall(".//trt:Profiles", NS):
            if prof.find("tt:PTZConfiguration", NS) is not None:
                self.profile_token = prof.get("token")
                break
        else:
            self.profile_token = tokens[0]

        for prof in root.findall(".//trt:Profiles", NS):
            source = prof.find("tt:VideoSourceConfiguration/tt:SourceToken", NS)
            if source is not None and source.text:
                self.video_source_token = source.text
                break

        try:
            nodes = await self._call(self._ptz_url, "<tptz:GetNodes/>")
            self.has_zoom = nodes.find(".//tt:ZoomLimits", NS) is not None
        except OnvifError:
            self.has_zoom = False

        await self._discover_imaging()

    async def _discover_imaging(self) -> None:
        """Work out whether the camera supports the IR filter and autofocus.

        GetOptions is tried first, since it lists what can actually be
        changed. Firmware often advertises the whole Imaging service
        while accepting only a fraction of its fields.
        """
        if not self.video_source_token:
            return

        try:
            root = await self._call(
                self._imaging_url,
                "<timg:GetOptions>"
                f"<timg:VideoSourceToken>{escape(self.video_source_token)}"
                "</timg:VideoSourceToken></timg:GetOptions>",
            )
            self.has_ir = root.find(".//tt:IrCutFilterModes", NS) is not None
            self.has_autofocus = root.find(".//tt:AutoFocusModes", NS) is not None

            for key, tag in (
                ("brightness", "Brightness"),
                ("color_saturation", "ColorSaturation"),
                ("contrast", "Contrast"),
                ("sharpness", "Sharpness"),
            ):
                node = root.find(f".//tt:{tag}", NS)
                if node is None:
                    continue
                low = node.find("tt:Min", NS)
                high = node.find("tt:Max", NS)
                if low is not None and high is not None and low.text and high.text:
                    self.imaging_ranges[key] = (float(low.text), float(high.text))
            _LOGGER.debug(
                "GetOptions on %s: ir=%s, autofocus=%s",
                self._host, self.has_ir, self.has_autofocus,
            )
        except OnvifError as err:
            _LOGGER.debug("GetOptions failed on %s: %s", self._host, err)

        if self.has_ir and self.has_autofocus:
            return

        try:
            settings = await self.get_imaging_settings()
        except OnvifError as err:
            _LOGGER.debug("GetImagingSettings failed on %s: %s", self._host, err)
            return

        if not self.has_ir and settings.get("ir_cut_filter"):
            self.has_ir = True
        if not self.has_autofocus and settings.get("autofocus"):
            self.has_autofocus = True

        _LOGGER.debug(
            "After GetImagingSettings on %s: ir=%s, autofocus=%s (raw values %s)",
            self._host, self.has_ir, self.has_autofocus, settings,
        )

    async def _read_device_info(self) -> None:
        try:
            root = await self._call(self._device_url, "<tds:GetDeviceInformation/>")
        except OnvifError:
            return
        model = root.find(".//tds:Model", NS)
        serial = root.find(".//tds:SerialNumber", NS)
        self.device_name = model.text if model is not None else None
        self.serial = serial.text if serial is not None else None


    async def continuous_move(
        self, pan: float = 0.0, tilt: float = 0.0, zoom: float = 0.0
    ) -> None:
        """Start moving at the given speed (-1.0 to 1.0)."""
        pan = max(-1.0, min(1.0, pan))
        tilt = max(-1.0, min(1.0, tilt))
        zoom = max(-1.0, min(1.0, zoom))

        velocity = f'<tt:PanTilt x="{pan:.3f}" y="{tilt:.3f}"/>'
        if self.has_zoom and zoom:
            velocity += f'<tt:Zoom x="{zoom:.3f}"/>'

        body = (
            "<tptz:ContinuousMove>"
            f"<tptz:ProfileToken>{escape(self.profile_token)}</tptz:ProfileToken>"
            f"<tptz:Velocity>{velocity}</tptz:Velocity>"
            "</tptz:ContinuousMove>"
        )
        await self._call(self._ptz_url, body)

    async def stop(self) -> None:
        body = (
            "<tptz:Stop>"
            f"<tptz:ProfileToken>{escape(self.profile_token)}</tptz:ProfileToken>"
            "<tptz:PanTilt>true</tptz:PanTilt>"
            "<tptz:Zoom>true</tptz:Zoom>"
            "</tptz:Stop>"
        )
        await self._call(self._ptz_url, body)

    async def move_for(
        self, pan: float, tilt: float, zoom: float, duration: float
    ) -> None:
        """Nudge in one direction, then stop. Used by the arrow buttons."""
        await self.continuous_move(pan, tilt, zoom)
        await asyncio.sleep(max(0.05, min(10.0, duration)))
        await self.stop()

    async def get_status(self) -> dict[str, float]:
        root = await self._call(
            self._ptz_url,
            "<tptz:GetStatus>"
            f"<tptz:ProfileToken>{escape(self.profile_token)}</tptz:ProfileToken>"
            "</tptz:GetStatus>",
        )
        pt = root.find(".//tt:PanTilt", NS)
        if pt is None:
            return {}
        return {
            "pan": float(pt.get("x", 0.0)),
            "tilt": float(pt.get("y", 0.0)),
        }

    async def get_presets(self) -> list[dict[str, str]]:
        root = await self._call(
            self._ptz_url,
            "<tptz:GetPresets>"
            f"<tptz:ProfileToken>{escape(self.profile_token)}</tptz:ProfileToken>"
            "</tptz:GetPresets>",
        )
        presets = []
        for node in root.findall(".//tptz:Preset", NS):
            name = node.find("tt:Name", NS)
            presets.append(
                {
                    "token": node.get("token", ""),
                    "name": name.text if name is not None else node.get("token", ""),
                }
            )
        return presets

    async def goto_preset(self, token: str, speed: float = 0.8) -> None:
        body = (
            "<tptz:GotoPreset>"
            f"<tptz:ProfileToken>{escape(self.profile_token)}</tptz:ProfileToken>"
            f"<tptz:PresetToken>{escape(token)}</tptz:PresetToken>"
            f'<tptz:Speed><tt:PanTilt x="{speed:.2f}" y="{speed:.2f}"/></tptz:Speed>'
            "</tptz:GotoPreset>"
        )
        await self._call(self._ptz_url, body)

    async def set_preset(self, name: str, token: str | None = None) -> str:
        body = (
            "<tptz:SetPreset>"
            f"<tptz:ProfileToken>{escape(self.profile_token)}</tptz:ProfileToken>"
            f"<tptz:PresetName>{escape(name)}</tptz:PresetName>"
        )
        if token:
            body += f"<tptz:PresetToken>{escape(token)}</tptz:PresetToken>"
        body += "</tptz:SetPreset>"
        root = await self._call(self._ptz_url, body)
        node = root.find(".//tptz:PresetToken", NS)
        return node.text if node is not None and node.text else ""


    async def get_imaging_settings(self) -> dict[str, object]:
        """Current IR filter state and focus mode."""
        if not self.video_source_token:
            return {}

        root = await self._call(
            self._imaging_url,
            "<timg:GetImagingSettings>"
            f"<timg:VideoSourceToken>{escape(self.video_source_token)}"
            "</timg:VideoSourceToken></timg:GetImagingSettings>",
        )
        ir = root.find(".//tt:IrCutFilter", NS)
        focus = root.find(".//tt:Focus/tt:AutoFocusMode", NS)

        result: dict[str, object] = {
            "ir_cut_filter": ir.text if ir is not None else None,
            "autofocus": focus.text if focus is not None else None,
        }

        for key, tag in (
            ("brightness", "Brightness"),
            ("color_saturation", "ColorSaturation"),
            ("contrast", "Contrast"),
            ("sharpness", "Sharpness"),
        ):
            node = root.find(f".//tt:{tag}", NS)
            if node is not None and node.text:
                try:
                    result[key] = float(node.text)
                except ValueError:
                    pass

        return result

    async def set_imaging(
        self,
        ir_cut_filter: str | None = None,
        autofocus: bool | None = None,
        **values: float | None,
    ) -> None:
        """Change picture settings.

        Keyword values: brightness, color_saturation, contrast and
        sharpness, plus ir_cut_filter and autofocus where the camera
        supports them.

        Two details that are easy to trip over:

        1. The element order inside ImagingSettings is fixed by the ONVIF
           schema. Break it and some firmware silently drops the whole
           request.
        2. SetImagingSettings replaces the settings wholesale rather than
           patching them, so missing fields are read back from the current
           values first. Otherwise adjusting brightness would zero out
           contrast.
        """
        if not self.video_source_token:
            raise OnvifError("The camera reported no video source")

        current = await self.get_imaging_settings()

        def pick(key: str) -> float | None:
            given = values.get(key)
            return given if given is not None else current.get(key)

        brightness = pick("brightness")
        saturation = pick("color_saturation")
        contrast = pick("contrast")
        sharpness = pick("sharpness")

        if autofocus is None:
            autofocus_mode = current.get("autofocus")
        else:
            autofocus_mode = "AUTO" if autofocus else "MANUAL"

        if ir_cut_filter is None:
            ir_mode = current.get("ir_cut_filter")
        else:
            ir_mode = str(ir_cut_filter).upper()
            if ir_mode not in ("ON", "OFF", "AUTO"):
                raise OnvifError(f"Invalid IR cut filter mode: {ir_cut_filter}")

        settings = ""
        if brightness is not None:
            settings += f"<tt:Brightness>{float(brightness):.0f}</tt:Brightness>"
        if saturation is not None:
            settings += f"<tt:ColorSaturation>{float(saturation):.0f}</tt:ColorSaturation>"
        if contrast is not None:
            settings += f"<tt:Contrast>{float(contrast):.0f}</tt:Contrast>"
        if autofocus_mode:
            settings += (
                f"<tt:Focus><tt:AutoFocusMode>{autofocus_mode}</tt:AutoFocusMode></tt:Focus>"
            )
        if ir_mode:
            settings += f"<tt:IrCutFilter>{ir_mode}</tt:IrCutFilter>"
        if sharpness is not None:
            settings += f"<tt:Sharpness>{float(sharpness):.0f}</tt:Sharpness>"

        if not settings:
            return

        body = (
            "<timg:SetImagingSettings>"
            f"<timg:VideoSourceToken>{escape(self.video_source_token)}"
            "</timg:VideoSourceToken>"
            f"<timg:ImagingSettings>{settings}</timg:ImagingSettings>"
            "<timg:ForcePersistence>true</timg:ForcePersistence>"
            "</timg:SetImagingSettings>"
        )
        await self._call(self._imaging_url, body)


    async def create_pullpoint(self, termination: str = "PT600S") -> str:
        """Create a pull point and return its address.

        The camera starts queueing events on its side; they must be
        collected with pull_messages or the subscription expires.
        """
        root = await self._call(
            self._events_url,
            "<tev:CreatePullPointSubscription>"
            f"<tev:InitialTerminationTime>{termination}</tev:InitialTerminationTime>"
            "</tev:CreatePullPointSubscription>",
            timeout=15,
        )
        address = root.find(".//tev:SubscriptionReference/wsa:Address", NS)
        if address is None or not address.text:
            address = root.find(".//wsa:Address", NS)
        if address is None or not address.text:
            raise OnvifError("The camera returned no subscription address")

        self._pullpoint_url = self._fix_host(address.text) or address.text
        self.has_events = True
        return self._pullpoint_url

    async def pull_messages(
        self, timeout_iso: str = "PT30S", limit: int = 10, http_timeout: int = 45
    ) -> list[dict[str, str]]:
        """Long poll: hang for up to timeout_iso until an event arrives.

        Returns a list of dicts holding the topic and its SimpleItem pairs.
        """
        if not self._pullpoint_url:
            raise OnvifError("No subscription has been created")

        root = await self._call(
            self._pullpoint_url,
            "<tev:PullMessages>"
            f"<tev:Timeout>{timeout_iso}</tev:Timeout>"
            f"<tev:MessageLimit>{limit}</tev:MessageLimit>"
            "</tev:PullMessages>",
            timeout=http_timeout,
        )

        events: list[dict[str, str]] = []
        for notification in root.findall(".//wsnt:NotificationMessage", NS):
            topic_node = notification.find("wsnt:Topic", NS)
            topic = "".join(topic_node.itertext()).strip() if topic_node is not None else ""

            items: dict[str, str] = {"topic": topic}
            for simple in notification.findall(".//tt:SimpleItem", NS):
                name = simple.get("Name")
                value = simple.get("Value")
                if name is not None and value is not None:
                    items[name] = value
            events.append(items)

        return events

    async def unsubscribe(self) -> None:
        if not self._pullpoint_url:
            return
        try:
            await self._call(
                self._pullpoint_url,
                '<Unsubscribe xmlns="http://docs.oasis-open.org/wsn/b-2"/>',
                timeout=10,
            )
        except OnvifError:
            pass
        finally:
            self._pullpoint_url = None

    async def get_stream_uri(self, profile_token: str | None = None) -> str | None:
        """The RTSP URL, useful for Generic Camera."""
        token = profile_token or self.profile_token
        body = (
            "<trt:GetStreamUri>"
            "<trt:StreamSetup>"
            "<tt:Stream>RTP-Unicast</tt:Stream>"
            "<tt:Transport><tt:Protocol>RTSP</tt:Protocol></tt:Transport>"
            "</trt:StreamSetup>"
            f"<trt:ProfileToken>{escape(token)}</trt:ProfileToken>"
            "</trt:GetStreamUri>"
        )
        try:
            root = await self._call(self._media_url, body)
        except OnvifError:
            return None
        uri = root.find(".//tt:Uri", NS)
        return uri.text if uri is not None else None
