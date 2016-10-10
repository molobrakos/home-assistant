"""Support for EnergyCount 3000 Energy loggers.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/ec3k/

Voltcraft Energycount 3000 is a relatively cheap wireless energy logger that
emits signals than can be received using a USB radio receiver and the GNU Radio
framework together with the ec3k python module.

Relevant Links
- Package
  https://github.com/avian2/ec3k
- Raspberry Pi setup:
  https://batilanblog.wordpress.com/2015/02/17/using-ec3k-with-raspberry-pi/
- Helper frequency scanner script
  https://github.com/molobrakos/ec3kscan

Due to the fact that the ec3k package depends on GNU Radio, which is
Python2-only, a Python2 environment with the ec3k package installed
has to be manually setup.

"""
import logging
import os
import threading
import subprocess
from functools import partial
from collections import defaultdict
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (ATTR_DISCOVERED,
                                 ATTR_SERVICE,
                                 EVENT_PLATFORM_DISCOVERED,
                                 EVENT_HOMEASSISTANT_STOP)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ec3k"

CONF_FREQUENCY = "frequency"
DEFAULT_FREQUENCY = 868.202

SENSORS = defaultdict(list)
STATES = {}

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_FREQUENCY, default=DEFAULT_FREQUENCY): vol.Coerce(float)
    }),
}, extra=vol.ALLOW_EXTRA)

def which(program, required=True):
    for path in os.environ["PATH"].split(os.pathsep):
        fpath = os.path.join(path, program)
        if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
            _LOGGER.info("Found %s: %s", program, fpath)
            return fpath
    [_LOGGER.warning, _LOGGER.error][required]\
        ("%s not found in path", program)

def setup(hass, config):
    """Set up the Ec3k sensors."""
    frequency = config[DOMAIN].get(CONF_FREQUENCY)
    _LOGGER.info("Using frequency %3.3f MHz", frequency)

    py2 = which("python2")
    receiver = which("ec3k_recv")
    if not py2 or not receiver:
        return False

    if not which("capture", required=False):
        if not which("capture.py"):
            return False
        else:
            _LOGGER.warning("Using capture.py. "
                            "Consider installing the faster C-implementation ")

    def run():
        _LOGGER.debug("Receiver thread started")
        args = [ py2, "-u", receiver, "--json", "--quiet" ]
        with subprocess.Popen(args, shell=False, 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT) as proc:
            _LOGGER.debug("Subprocess started")
            for line in proc.stdout:
                _LOGGER.debug(line.decode('ascii'))

    threading.Thread(target=run).start()

    def shutdown(event):
        """Shutdown the platform."""
        _LOGGER.debug("shutting down platform")

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, shutdown)
    return True
