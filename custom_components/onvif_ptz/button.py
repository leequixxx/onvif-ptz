"""Direction buttons.

These exist for the auto-generated Overview: a custom card cannot be
placed there, while plain entities are laid out by the original-states
strategy on its own. The joystick stays for dashboards taken over.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Coroutine, Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_SPEED, DEFAULT_STEP_DURATION, DOMAIN
from .soap import OnvifError, OnvifPtzClient


@dataclass(frozen=True, kw_only=True)
class PtzButtonDescription(ButtonEntityDescription):
    """A button description bundled with the action it performs."""

    action: Callable[[OnvifPtzClient], Coroutine[Any, Any, None]]


def _step(pan: float, tilt: float):
    async def _run(client: OnvifPtzClient) -> None:
        await client.move_for(pan, tilt, 0.0, DEFAULT_STEP_DURATION)

    return _run


async def _stop(client: OnvifPtzClient) -> None:
    await client.stop()


BUTTONS: tuple[PtzButtonDescription, ...] = (
    PtzButtonDescription(
        key="left",
        translation_key="left",
        icon="mdi:arrow-left-bold",
        action=_step(-DEFAULT_SPEED, 0.0),
    ),
    PtzButtonDescription(
        key="right",
        translation_key="right",
        icon="mdi:arrow-right-bold",
        action=_step(DEFAULT_SPEED, 0.0),
    ),
    PtzButtonDescription(
        key="up",
        translation_key="up",
        icon="mdi:arrow-up-bold",
        action=_step(0.0, DEFAULT_SPEED),
    ),
    PtzButtonDescription(
        key="down",
        translation_key="down",
        icon="mdi:arrow-down-bold",
        action=_step(0.0, -DEFAULT_SPEED),
    ),
    PtzButtonDescription(
        key="stop",
        translation_key="stop",
        icon="mdi:stop",
        action=_stop,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: OnvifPtzClient = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PtzButton(client, entry, description) for description in BUTTONS
    )


class PtzButton(ButtonEntity):
    """One press nudges the camera briefly."""

    _attr_has_entity_name = True
    entity_description: PtzButtonDescription

    def __init__(
        self,
        client: OnvifPtzClient,
        entry: ConfigEntry,
        description: PtzButtonDescription,
    ) -> None:
        self._client = client
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
        )

    async def async_press(self) -> None:
        from homeassistant.exceptions import HomeAssistantError

        try:
            await self.entity_description.action(self._client)
        except OnvifError as err:
            raise HomeAssistantError(str(err)) from err
