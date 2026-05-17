from gpioctrl import Pi, Dummy
import sounddevice as SD
import soundfile as SF
import logging
import time

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
    def play(self, stop_ts:float=None):
        '''Play the pre-loaded music file. Optionally, a float value can be supplied for stop_ts and the music will stop at the provided timestamp.
        
        Do not that if a stop_ts is provided, this function will hold the main thread until the stop_ts is reached.'''
        if self.GPIO: self.GPIO.HIGH()
        SD.play(self.data, self.samplerate)
        log.debug(f"MusicBox is now playing")
        if stop_ts:
            if isinstance(stop_ts, float):
                log.debug(f"Playback will be stopped in {stop_ts - time.time()} seconds.")
                while time.time() < stop_ts:
                    time.sleep(0.05)
                log.debug(f"Stopping playback.")
                self.stop()
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
    testbox.play(stop_ts=time.time() + 5)