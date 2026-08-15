"""Brightness, saturation, contrast and sharpness.

Only the controls the camera listed in GetOptions are created: the set of
supported settings varies widely between firmware versions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
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

SCAN_INTERVAL = timedelta(seconds=60)


@dataclass(frozen=True, kw_only=True)
class ImagingNumber(NumberEntityDescription):
    """A number description bundled with its key in the camera settings."""

    setting: str


NUMBERS: tuple[ImagingNumber, ...] = (
    ImagingNumber(
        key="brightness",
        setting="brightness",
        translation_key="brightness",
        icon="mdi:brightness-6",
    ),
    ImagingNumber(
        key="color_saturation",
        setting="color_saturation",
        translation_key="color_saturation",
        icon="mdi:palette",
    ),
    ImagingNumber(
        key="contrast",
        setting="contrast",
        translation_key="contrast",
        icon="mdi:contrast-circle",
    ),
    ImagingNumber(
        key="sharpness",
        setting="sharpness",
        translation_key="sharpness",
        icon="mdi:blur",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: OnvifPtzClient = hass.data[DOMAIN][entry.entry_id]

    if not client.imaging_ranges:
        _LOGGER.debug("Camera %s reported no picture setting ranges", entry.title)
        return

    async def _fetch() -> dict[str, object]:
        try:
            return await client.get_imaging_settings()
        except OnvifError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_picture_{entry.entry_id}",
        update_method=_fetch,
        update_interval=SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        ImagingNumberEntity(coordinator, client, entry, description)
        for description in NUMBERS
        if description.setting in client.imaging_ranges
    )


class ImagingNumberEntity(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 1
    entity_description: ImagingNumber

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: OnvifPtzClient,
        entry: ConfigEntry,
        description: ImagingNumber,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self.entity_description = description

        low, high = client.imaging_ranges[description.setting]
        self._attr_native_min_value = low
        self._attr_native_max_value = high

        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
        )

    @property
    def native_value(self) -> float | None:
        value = (self.coordinator.data or {}).get(self.entity_description.setting)
        return float(value) if isinstance(value, (int, float)) else None

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self._client.set_imaging(**{self.entity_description.setting: value})
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()
