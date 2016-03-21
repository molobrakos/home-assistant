"""
Support for EnergyCount 3000 Energy loggers.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/ec3k/

Voltcraft Energycount 3000 is a relatively cheap wireless energy logger that
emits signals than can be received using a USB radio receiver and the GNU Radio
framework together with the ec3k python module.

Relevant Links
- Package
  https://pypi.python.org/pypi/ec3k/
- Package source
  https://github.com/avian2/ec3k
- Raspberry Pi setup:
  https://batilanblog.wordpress.com/2015/02/17/using-ec3k-with-raspberry-pi/
- Helper frequency scanner script
  https://github.com/molobrakos/ec3kscan
"""
import logging
from functools import partial
from collections import defaultdict

from homeassistant.const import (ATTR_DISCOVERED,
                                 ATTR_SERVICE,
                                 EVENT_PLATFORM_DISCOVERED,
                                 EVENT_HOMEASSISTANT_STOP)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ec3k"
REQUIREMENTS = ['ec3k']
DEPENDENCIES = ['sensor', 'binary_sensor']

DISCOVER_SENSORS = "ec3k.sensors"
DISCOVER_BINARY_SENSORS = "ec3k.binary_sensors"

CONF_FREQUENCY = "frequency"
DEFAULT_FREQUENCY = 868.202  # MHz

#  global state { id: [ sensors ] }
SENSORS = defaultdict(list)

#  global state { id: current_state }
STATES = {}

EC3K_RECEIVER = None


def ec3k_callback(hass, config, state):
    """Called by the ec3k package when new signal is detected."""
    _LOGGER.debug("received ec3k signal from %04x", state.id)

    known_id = state.id in STATES
    STATES[state.id] = state

    if known_id:
        for sensor in SENSORS[state.id]:
            sensor.update_ha_state()
    else:
        _LOGGER.info("New ec3k device %04x detected", state.id)
        hass.bus.fire(EVENT_PLATFORM_DISCOVERED,
                      {ATTR_SERVICE: DISCOVER_SENSORS,
                       ATTR_DISCOVERED: state.id})
        hass.bus.fire(EVENT_PLATFORM_DISCOVERED,
                      {ATTR_SERVICE: DISCOVER_BINARY_SENSORS,
                       ATTR_DISCOVERED: state.id})


def mock_listen(callback):
    """Fake some receivers. Useful for developing on """
    from random import choice, randint
    from time import sleep
    from types import SimpleNamespace
    ids = [42, 4711]
    _LOGGER.info("Faking ec3k events")
    while True:
        sleep(1)
        _LOGGER.info("Faking ec3k state change")
        callback(SimpleNamespace(
            id=choice(ids),
            device_on_flag=randint(0, 1),
            time_total=0,
            time_on=0,
            energy=randint(1e6, 1e8),
            power_current=randint(0, 1e3),
            power_max=0,
            reset_counter=0))


def setup(hass, config):
    """Set up the Ec3k sensors."""
    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, shutdown)

    callback = partial(ec3k_callback, hass, config)
    frequency = config.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)
    _LOGGER.info("Using frequency %3.3f MHz for ec3k loggers", frequency)

    if config[DOMAIN].get("mock"):
        from threading import Thread
        Thread(target=lambda: mock_listen(callback)).start()
        return True

    try:
        import ec3k
        global EC3K_RECEIVER
        EC3K_RECEIVER = ec3k.EnergyCount(callback=callback,
                                         frequency=frequency * 1e6)
        EC3K_RECEIVER._log = _LOGGER.log#lambda self, msg: _LOGGER.log(msg)
        EC3K_RECEIVER.start()
        return True
    except (ImportError, SyntaxError):
        _LOGGER.error("failed to initialize ec3k module")
        return False


def shutdown(event):
    """Shutdown the platform."""
    _LOGGER.debug("shutting down platform")
    if EC3K_RECEIVER:
        _LOGGER.debug("stopping ec3k receiver")
        EC3K_RECEIVER.stop()
        _LOGGER.debug("ec3k receiver stopped")
