import logging
import time

log = logging.getLogger("GPIO Control")

class Pi():
    def __init__(self, pins:list=[]):
        self.pins = pins
        log.debug(f"Setting up Raspberry Pi GPIO for pins {self.pins}")
        import RPi.GPIO as GPIO # type: ignore
        self.GPIO = GPIO
        for pin in self.pins:
            log.debug(f"Setting up pin {pin}")
            self.GPIO.setup(pin, self.GPIO.OUT)
            self.GPIO.output(pin, self.GPIO.LOW) # reset to low
        # perform self test
        self.HIGH()
        time.sleep(0.5)
        self.LOW()
        log.debug(f"Init self-test complete")
    def HIGH(self):
        log.debug(f"Outputting pins {self.pins} to HIGH")
        for pin in self.pins:
            log.debug(f"Pin {pin} is HIGH")
            self.GPIO.output(pin, self.GPIO.HIGH)
    def LOW(self):
        log.debug(f"Outputting pins {self.pins} to LOW")
        for pin in self.pins:
            log.debug(f"Pin {pin} is LOW")
            self.GPIO.output(pin, self.GPIO.LOW)

class Dummy():
    def __init__(self, pins:list=[]):
        log.debug(f"Dummy GPIO class initialized, no activity will occur.")
    def HIGH(self):
        pass
    def LOW(self):
        pass

if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(level="DEBUG")
    try:
        GPIO = Pi([4, 22, 6, 26])
    except:
        GPIO = Dummy()