import pigpio
from threading import Timer, Lock


from logging import getLogger

logger = getLogger(__name__)


class Switch:
    """
    Represents a switch connected to a Raspberry Pi GPIO pin.

    Args:
        pin (int): The GPIO pin number.
        pi (pigpio.pi): An instance of the pigpio.pi class representing the Raspberry Pi.
        debounce_interval (float, optional): The debounce interval in seconds. Defaults to 0.2.
        pud (int, optional): The pull-up/pull-down configuration. Defaults to pigpio.PUD_UP.
        edge (int, optional): The edge detection configuration. Defaults to pigpio.EITHER_EDGE.
    """

    def __init__(
        self,
        pin,
        pi: pigpio.pi,
        debounce_interval: float = 0.2,
        pud=pigpio.PUD_UP,
        edge=pigpio.EITHER_EDGE,
    ):
        self._pin = pin
        self._timer = None
        self._lock = Lock()

        self._debounce_interval = debounce_interval
        self._edge = edge

        self._pi = pi
        with self._lock:
            self._pi.set_mode(self._pin, pigpio.INPUT)
            self._pi.set_pull_up_down(self._pin, pud)
            self._h_pi_cbk = self._pi.callback(
                self._pin, pigpio.EITHER_EDGE, self._pigpio_callback
            )
            self._level = self._pi.read(self._pin)

    def _pigpio_callback(self, gpio, level, tick):
        logger.debug(f"gpio:{self._pin}, level:{level}, tick:{tick}")
        with self._lock:
            if isinstance(self._timer, Timer):
                self._timer.cancel()
            self._timer = Timer(
                self._debounce_interval, self._callback, args=(level, tick)
            )
            self._timer.start()

    def _callback(self, level, tick):

        with self._lock:
            self._level = level
            if isinstance(self._timer, Timer):
                self._timer.cancel()
                self._timer = None
        if (
            self._edge == pigpio.EITHER_EDGE
            or (self._edge == pigpio.RISING_EDGE and level)
            or (self._edge == pigpio.FALLING_EDGE and not level)
        ):
            self.callback(self._pin, level, tick)

    def __del__(self):
        self.cancel()

    @property
    def pin(self):
        return self._pin

    @property
    def level(self):
        return self._level

    def read(self):
        return self._pi.read(self._pin)

    def cancel(self):
        with self._lock:
            if self._timer is not None and isinstance(self._timer, Timer):
                self._timer.cancel()
                self._timer = None

        if self._h_pi_cbk is not None and isinstance(self._h_pi_cbk, pigpio._callback):
            self._h_pi_cbk.cancel()
            self._h_pi_cbk = None

        if self._pi is not None:
            if isinstance(self._pi, pigpio.pi):
                self._pi.set_pull_up_down(self._pin, pigpio.PUD_OFF)
            self._pi = None

    def callback(self, gpio, level, tick):
        pass


#
# Rest of the code...
if __name__ == "__main__":
    pi = pigpio.pi()
    try:
        switch = Switch(17, pi)  # Replace 17 with the GPIO pin number you are using
        while True:
            pass
    finally:
        pi.stop()

# Keep the program running to continue detecting switch state
# Press Ctrl+C to stop the program
