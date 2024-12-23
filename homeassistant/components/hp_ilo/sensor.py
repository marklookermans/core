from datetime import timedelta
import logging

import hpilo

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PORT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import Throttle

from .const import DOMAIN, SENSOR_TYPES, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)

async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigType, async_add_entities: AddEntitiesCallback
):
    """Set up HP iLO sensors from a config entry."""
    config = hass.data[DOMAIN][config_entry.entry_id]

    hostname = config[CONF_HOST]
    port = config[CONF_PORT]
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]

    # Initialize data fetcher
    hp_ilo_data = HpIloData(hostname, port, username, password)

    # Create sensors based on the available SENSOR_TYPES
    devices = []
    for sensor_type, sensor_info in SENSOR_TYPES.items():
        devices.append(
            HpIloSensor(
                hp_ilo_data=hp_ilo_data,
                sensor_name=f"{DEFAULT_NAME} {sensor_info[0]}",
                sensor_type=sensor_type,
            )
        )

    async_add_entities(devices, True)


class HpIloSensor(SensorEntity):
    """Representation of an HP iLO sensor."""

    def __init__(self, hp_ilo_data, sensor_type, sensor_name):
        """Initialize the HP iLO sensor."""
        self._name = sensor_name
        self._ilo_function = SENSOR_TYPES[sensor_type][1]
        self.hp_ilo_data = hp_ilo_data
        self._state = None
        self._state_attributes = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        return self._state_attributes

    def update(self):
        """Get the latest data from HP iLO and update the state."""
        self.hp_ilo_data.update()
        ilo_data = getattr(self.hp_ilo_data.data, self._ilo_function)()
        self._state = ilo_data


class HpIloData:
    """Gets the latest data from HP iLO."""

    def __init__(self, host, port, username, password):
        """Initialize the data object."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password

        self.data = None
        self.update()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from HP iLO."""
        try:
            self.data = hpilo.Ilo(
                hostname=self._host,
                login=self._username,
                password=self._password,
                port=self._port,
            )
        except (
            hpilo.IloError,
            hpilo.IloCommunicationError,
            hpilo.IloLoginFailed,
        ) as error:
            _LOGGER.error("Unable to fetch data from HP iLO: %s", error)
