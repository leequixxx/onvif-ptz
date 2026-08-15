"""The IR cut filter and autofocus as switches.

Both settings live in the ONVIF Imaging service and are addressed by
video source rather than by profile. Cameras support them selectively,
so the entities are created only once GetOptions has confirmed them.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .soap import OnvifError, OnvifPtzClient

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: OnvifPtzClient = hass.data[DOMAIN][entry.entry_id]

    if not (client.has_ir or client.has_autofocus):
        _LOGGER.debug("Camera %s does not support Imaging, no switches will be created", entry.title)
        return

    async def _fetch() -> dict[str, str | None]:
        try:
            return await client.get_imaging_settings()
        except OnvifError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_imaging_{entry.entry_id}",
        update_method=_fetch,
        update_interval=SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()

    entities: list[SwitchEntity] = []
    if client.has_ir:
        entities.append(NightModeSwitch(coordinator, client, entry))
    if client.has_autofocus:
        entities.append(AutofocusSwitch(coordinator, client, entry))

    async_add_entities(entities)


class _Base(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: OnvifPtzClient,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
        )


class NightModeSwitch(_Base):
    """Night mode.

    In ONVIF this is IrCutFilter, and it reads backwards: ON means the cut
    filter is in place, which is daytime colour. OFF lets infrared through
    and turns on night vision. The entity is presented in plain terms and
    the translation happens here.
    """

    _attr_translation_key = "night_mode"
    _attr_icon = "mdi:weather-night"

    def __init__(self, coordinator, client, entry) -> None:
        super().__init__(coordinator, client, entry, "night_mode")

    @property
    def is_on(self) -> bool | None:
        value = (self.coordinator.data or {}).get("ir_cut_filter")
        if value is None:
            return None
        return value.upper() == "OFF"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        value = (self.coordinator.data or {}).get("ir_cut_filter")
        return {"ir_cut_filter": value} if value else {}

    async def async_turn_on(self, **kwargs) -> None:
        await self._apply("OFF")

    async def async_turn_off(self, **kwargs) -> None:
        await self._apply("ON")

    async def _apply(self, mode: str) -> None:
        try:
            await self._client.set_imaging(ir_cut_filter=mode)
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()


class AutofocusSwitch(_Base):
    _attr_translation_key = "autofocus"
    _attr_icon = "mdi:focus-auto"

    def __init__(self, coordinator, client, entry) -> None:
        super().__init__(coordinator, client, entry, "autofocus")

    @property
    def is_on(self) -> bool | None:
        value = (self.coordinator.data or {}).get("autofocus")
        if value is None:
            return None
        return value.upper() == "AUTO"

    async def async_turn_on(self, **kwargs) -> None:
        await self._apply(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._apply(False)

    async def _apply(self, enabled: bool) -> None:
        try:
            await self._client.set_imaging(autofocus=enabled)
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()
