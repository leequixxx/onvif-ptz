"""ONVIF PTZ integration - pan-tilt control for a camera.

Deliberately creates no camera entity and never reads media profiles.
Take the video through Generic Camera or go2rtc; movement is all that
happens here. That is what lets the integration work with firmware that
returns an empty VideoEncoderConfiguration, where the built-in ONVIF
integration fails with "There were no H.264 streams available".
"""

from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ATTR_DURATION,
    ATTR_ENTRY_ID,
    ATTR_NAME,
    ATTR_PAN,
    ATTR_PRESET,
    ATTR_TILT,
    ATTR_ZOOM,
    DEFAULT_SPEED,
    DEFAULT_STEP_DURATION,
    DOMAIN,
    SERVICE_GOTO_PRESET,
    SERVICE_MOVE,
    SERVICE_SET_PRESET,
    SERVICE_STEP,
    SERVICE_STOP,
)
from .soap import OnvifError, OnvifPtzClient

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL = "/onvif_ptz_frontend"
FRONTEND_FILE = "onvif-ptz-card.js"
CARD_VERSION = "2.4.0"

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BINARY_SENSOR,
]

_SPEED = vol.All(vol.Coerce(float), vol.Range(min=-1.0, max=1.0))

MOVE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_PAN, default=0.0): _SPEED,
        vol.Optional(ATTR_TILT, default=0.0): _SPEED,
        vol.Optional(ATTR_ZOOM, default=0.0): _SPEED,
    }
)

STEP_SCHEMA = MOVE_SCHEMA.extend(
    {
        vol.Optional(ATTR_DURATION, default=DEFAULT_STEP_DURATION): vol.All(
            vol.Coerce(float), vol.Range(min=0.05, max=10.0)
        ),
    }
)

STOP_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string})

GOTO_PRESET_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Required(ATTR_PRESET): cv.string,
    }
)

SET_PRESET_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_PRESET): cv.string,
    }
)


async def _register_frontend(hass: HomeAssistant) -> None:
    """Serve the card file and attach it to the dashboard."""
    if hass.data.get(f"{DOMAIN}_frontend_ready"):
        return
    hass.data[f"{DOMAIN}_frontend_ready"] = True

    directory = Path(__file__).parent / "frontend"

    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_URL, str(directory), False)]
        )
    except ImportError:
        hass.http.register_static_path(FRONTEND_URL, str(directory), False)

    from homeassistant.components.frontend import add_extra_js_url

    add_extra_js_url(
        hass, f"{FRONTEND_URL}/{FRONTEND_FILE}?v={CARD_VERSION}"
    )
    _LOGGER.debug("Card registered at %s", FRONTEND_URL)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Bring up the connection to the camera."""
    await _register_frontend(hass)

    client = OnvifPtzClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=async_get_clientsession(hass),
    )

    try:
        await client.async_setup()
    except OnvifError as err:
        raise ConfigEntryNotReady(f"Camera {entry.data[CONF_HOST]}: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
        manufacturer="ONVIF",
        model=client.device_name or "PTZ camera",
        name=entry.title,
        configuration_url=f"http://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}",
    )

    _register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _stop_on_shutdown(_event) -> None:
        try:
            await client.stop()
        except OnvifError:
            pass

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _stop_on_shutdown)
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the entry and, if it was the last one, drop the services."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    client: OnvifPtzClient | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if client is not None:
        try:
            await client.stop()
        except OnvifError:
            pass

    if not hass.data.get(DOMAIN):
        for service in (
            SERVICE_MOVE,
            SERVICE_STOP,
            SERVICE_STEP,
            SERVICE_GOTO_PRESET,
            SERVICE_SET_PRESET,
        ):
            hass.services.async_remove(DOMAIN, service)

    return True


def _resolve(hass: HomeAssistant, call: ServiceCall) -> OnvifPtzClient:
    """Resolve the camera: by entry_id, or the only loaded one."""
    clients: dict[str, OnvifPtzClient] = hass.data.get(DOMAIN, {})
    if not clients:
        raise HomeAssistantError("No PTZ camera is set up")

    entry_id = call.data.get(ATTR_ENTRY_ID)
    if entry_id:
        client = clients.get(entry_id)
        if client is None:
            raise HomeAssistantError(f"No camera found with entry_id={entry_id}")
        return client

    if len(clients) > 1:
        raise HomeAssistantError(
            "Several cameras are set up - pass entry_id in the service call"
        )
    return next(iter(clients.values()))


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_MOVE):
        return

    async def handle_move(call: ServiceCall) -> None:
        client = _resolve(hass, call)
        try:
            await client.continuous_move(
                call.data[ATTR_PAN], call.data[ATTR_TILT], call.data[ATTR_ZOOM]
            )
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err

    async def handle_stop(call: ServiceCall) -> None:
        client = _resolve(hass, call)
        try:
            await client.stop()
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err

    async def handle_step(call: ServiceCall) -> None:
        client = _resolve(hass, call)
        try:
            await client.move_for(
                call.data[ATTR_PAN],
                call.data[ATTR_TILT],
                call.data[ATTR_ZOOM],
                call.data[ATTR_DURATION],
            )
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err

    async def handle_goto_preset(call: ServiceCall) -> None:
        client = _resolve(hass, call)
        try:
            await client.goto_preset(call.data[ATTR_PRESET], DEFAULT_SPEED)
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err

    async def handle_set_preset(call: ServiceCall) -> None:
        client = _resolve(hass, call)
        try:
            token = await client.set_preset(
                call.data[ATTR_NAME], call.data.get(ATTR_PRESET)
            )
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err
        _LOGGER.info("Preset saved, token %s", token)

    hass.services.async_register(DOMAIN, SERVICE_MOVE, handle_move, MOVE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop, STOP_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STEP, handle_step, STEP_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_GOTO_PRESET, handle_goto_preset, GOTO_PRESET_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_PRESET, handle_set_preset, SET_PRESET_SCHEMA
    )
