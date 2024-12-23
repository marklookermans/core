import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_PORT

from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)


class HpIloConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HP iLO."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._errors = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        self._errors = {}

        if user_input is not None:
            # Validate user input
            valid = await self._test_connection(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )
            else:
                self._errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=self._errors
        )

    async def _test_connection(self, host, port, username, password):
        """Test the connection to the HP iLO API."""
        try:
            # Attempt to initialize a connection
            from hpilo import Ilo

            Ilo(hostname=host, login=username, password=password, port=port)
            return True
        except Exception as e:  # Catch all exceptions for now
            _LOGGER.error("Failed to connect to HP iLO: %s", str(e))
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return HpIloOptionsFlowHandler(config_entry)


class HpIloOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for HP iLO."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_HOST, default=self.config_entry.data.get(CONF_HOST)
                ): str,
                vol.Optional(
                    CONF_PORT, default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
