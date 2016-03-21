"""
Support for Ec3k energy counter sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.ec3k/
"""

import logging
from homeassistant.helpers.entity import Entity
from homeassistant.components import ec3k

_LOGGER = logging.getLogger(__name__)

ATTR_IS_ON = "is_on"
ATTR_POWER = "power"
ATTR_TIME_TOTAL = "total_time"
ATTR_TIME_ON = "time_on"
ATTR_ENERGY = "energy"
ATTR_POWER_MAX = "max_power"

UNIT_OF_MEASUREMENT = {
    ATTR_POWER: "W",
    ATTR_ENERGY: "kWh"
}

ICON = "mdi:speedometer"


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Ec3k sensors."""
    _LOGGER.debug("new ec3k sensor")

    if discovery_info is None:
        _LOGGER.error("expected discovery info")
        return

    sensor_id = discovery_info
    monitored_attrs = [ATTR_POWER, ATTR_ENERGY]
    sensors = [Ec3kSensor(sensor_id, attr) for attr in monitored_attrs]
    add_devices(sensors)
    ec3k.SENSORS[sensor_id].extend(sensors)


class Ec3kSensor(Entity):
    """Implements a Ec3k sensor."""

    def __init__(self, sensor_id, monitored_attr):
        """Initialize the sensor."""
        self._id = sensor_id
        self._monitored_attr = monitored_attr

    @property
    def _state(self):
        """Retrieve the current state."""
        return ec3k.STATES.get(self._id)

    @property
    def state(self):
        """Return the state of the entity."""
        return self.state_attributes[self._monitored_attr]

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return False

    @property
    def name(self):
        """Return the name of the entity."""
        return "EnergyCounter %04x %s" % (self._id, self._monitored_attr)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return UNIT_OF_MEASUREMENT[self._monitored_attr]

    @property
    def state_attributes(self):
        """Return device specific state attributes."""
        attr = super().state_attributes or {}
        attr.update({
            ATTR_IS_ON: self._state.device_on_flag,
            ATTR_POWER: self._state.power_current,
            ATTR_TIME_TOTAL: self._state.time_total,
            ATTR_TIME_ON: self._state.time_on,
            ATTR_ENERGY: round(self._state.energy / 1e3 / 3600, 1),  # Ws -> kWh
            ATTR_POWER_MAX: self._state.power_max
        })
        return attr
