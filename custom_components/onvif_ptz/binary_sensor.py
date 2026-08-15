"""Motion detection over an ONVIF pull point.

The camera queues events on its side and they are collected by long
polling: the request hangs for up to 30 seconds and returns either with
an event or empty. That is cheaper than frequent polling and gives
sub-second latency.

A subscription has a limited lifetime and is recreated on every drop -
cheap firmware loses it at the slightest network hiccup.
"""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .soap import OnvifError, OnvifPtzClient

_LOGGER = logging.getLogger(__name__)

MOTION_KEYS = ("IsMotion", "State", "Motion", "IsMotionDetected", "isMotion")
MOTION_TOPICS = ("Motion", "MotionAlarm", "CellMotionDetector", "MotionDetect")

MOTION_TIMEOUT = 30

RECONNECT_MIN = 5
RECONNECT_MAX = 120


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: OnvifPtzClient = hass.data[DOMAIN][entry.entry_id]
    sensor = MotionSensor(client, entry)
    async_add_entities([sensor])


class MotionSensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "motion"
    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_should_poll = False

    def __init__(self, client: OnvifPtzClient, entry: ConfigEntry) -> None:
        self._client = client
        self._entry = entry
        self._state = False
        self._available = False
        self._task: asyncio.Task | None = None
        self._off_timer: asyncio.TimerHandle | None = None

        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_motion"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
        )

    @property
    def is_on(self) -> bool:
        return self._state

    @property
    def available(self) -> bool:
        return self._available

    async def async_added_to_hass(self) -> None:
        self._task = self.hass.async_create_background_task(
            self._listen(), name=f"{DOMAIN}_motion_{self._entry.entry_id}"
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None
        self._cancel_off_timer()
        await self._client.unsubscribe()


    async def _listen(self) -> None:
        """Hold the subscription and parse the event stream."""
        backoff = RECONNECT_MIN

        while True:
            try:
                await self._client.create_pullpoint()
            except OnvifError as err:
                if self._available:
                    self._available = False
                    self.async_write_ha_state()
                _LOGGER.debug("Event subscription could not be created: %s", err)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, RECONNECT_MAX)
                continue

            self._available = True
            self.async_write_ha_state()
            backoff = RECONNECT_MIN

            try:
                while True:
                    events = await self._client.pull_messages()
                    for event in events:
                        self._handle(event)
            except asyncio.CancelledError:
                raise
            except OnvifError as err:
                _LOGGER.debug("Event polling interrupted (%s), resubscribing", err)
                await self._client.unsubscribe()
                await asyncio.sleep(2)

    @callback
    def _handle(self, event: dict[str, str]) -> None:
        topic = event.get("topic", "")
        if not any(marker in topic for marker in MOTION_TOPICS):
            return

        raw = next((event[key] for key in MOTION_KEYS if key in event), None)
        if raw is None:
            return

        state = str(raw).strip().lower() in ("true", "1", "on", "active")
        self._set_state(state)

    @callback
    def _set_state(self, state: bool) -> None:
        self._cancel_off_timer()

        if state:
            self._off_timer = self.hass.loop.call_later(
                MOTION_TIMEOUT, self._expire
            )

        if state != self._state:
            self._state = state
            self.async_write_ha_state()

    @callback
    def _expire(self) -> None:
        self._off_timer = None
        if self._state:
            self._state = False
            self.async_write_ha_state()

    @callback
    def _cancel_off_timer(self) -> None:
        if self._off_timer:
            self._off_timer.cancel()
            self._off_timer = None
