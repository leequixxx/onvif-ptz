"""Camera setup through the Home Assistant UI."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN
from .soap import OnvifError, OnvifPtzClient

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_NAME): str,
    }
)


class OnvifPtzConfigFlow(ConfigFlow, domain=DOMAIN):
    """A single step: address and credentials, then a PTZ check."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            client = OnvifPtzClient(
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=async_get_clientsession(self.hass),
            )

            try:
                await client.async_setup()
                await client.get_status()
            except OnvifError as err:
                message = str(err)
                if "NotAuthorized" in message or "Fault" in message:
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
                _LOGGER.debug("Camera validation failed: %s", message)
            else:
                unique = client.serial or f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()

                title = (
                    user_input.get(CONF_NAME)
                    or client.device_name
                    or f"PTZ {user_input[CONF_HOST]}"
                )
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=SCHEMA, errors=errors
        )
