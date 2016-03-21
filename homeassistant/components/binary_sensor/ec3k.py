"""
Support for Ec3k sensor.

For more details about this platform, please refer to the documentation at
at https://home-assistant.io/components/sensor.ec3k/
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.components import ec3k
from homeassistant.components.sensor.ec3k import (
    ATTR_IS_ON, ATTR_POWER, ATTR_TIME_TOTAL,
    ATTR_TIME_ON, ATTR_ENERGY, ATTR_POWER_MAX)


DEPENDENCIES = ['ec3k']
_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Ec3k platform."""
    _LOGGER.info("setup platform")

    if discovery_info is None:
        _LOGGER.error("expected discovery info")
        return

    sensor_id = discovery_info
    sensor = Ec3kBinarySensor(sensor_id)
    add_devices([sensor])
    ec3k.SENSORS[sensor_id].append(sensor)


class Ec3kBinarySensor(BinarySensorDevice):
    """Implements a Ec3k sensor."""

    def __init__(self, sensor_id):
        """Initialize the sensor."""
        self._id = sensor_id

    @property
    def _state(self):
        """Return the global state."""
        return ec3k.STATES.get(self._id)

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._state.device_on_flag

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return False

    @property
    def name(self):
        """Return the name of the entity."""
        return "EnergyCounter %04x state" % self._id

    @property
    def state_attributes(self):
        """Return device specific state attributes."""
        attr = super().state_attributes or {}
        attr.update({
            ATTR_IS_ON: self._state.device_on_flag,
            ATTR_POWER: self._state.power_current,
            ATTR_TIME_TOTAL: self._state.time_total,
            ATTR_TIME_ON: self._state.time_on,
            ATTR_ENERGY: self._state.energy / 1e3,  # kWh
            ATTR_POWER_MAX: self._state.power_max
        })
        return attr
