from gpioctrl import Pi, Dummy
import sounddevice as SD
import soundfile as SF
import logging

log = logging.getLogger(__name__)

class MusicBox():
    def __init__(self, device_id, gpio:bool=True, gpio_pins:list=[]):
        self.data = None
        self.samplerate = None
        self.GPIO = None
        try:
            SD.default.device = device_id
        except Exception as E:
            log.error(f"Error trying to define default sound device. {E}")
        if gpio == True:
            try:
                self.GPIO = Pi(gpio_pins)
                log.info("MusicBox GPIO control configured for Raspberry Pi.")
            except:
                log.info("MusicBox GPIO control is not supported on this device.")
                self.GPIO = Dummy(gpio_pins) 
    def load(self, filepath:str):
        self.data, self.samplerate = SF.read(filepath, dtype="float32")
        log.debug(f"Loaded file '{filepath}' and ready for playback")
    def play(self):
        if self.GPIO: self.GPIO.HIGH()
        SD.play(self.data, self.samplerate)
        log.debug(f"MusicBox is now playing")
    def stop(self):
        SD.stop()
        if self.GPIO: self.GPIO.LOW()
        log.debug(f"MusicBox has stopped playing")


if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(level="DEBUG")
    testbox = MusicBox(device_id="Speakers (2- USB Audio Device), MME")
    testfile = "playlists/default/Tortilla Flat.mp3"
    testbox.load(testfile)
    testbox.play()
    import time
    time.sleep(5)
    testbox.stop()