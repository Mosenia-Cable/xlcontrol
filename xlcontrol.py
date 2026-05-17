import os, sys, json, requests, time
import logging
from telftpman2 import TelFTPMan
PROGRAM_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROGRAM_PATH)

log = logging.getLogger(__name__)

COMMON = {}
PRESENTATIONS = {}
TFM = TelFTPMan(autostart=False)

def load_settings():
    '''Loads common.json dictionary'''
    global COMMON
    common_path = os.path.join(PROGRAM_PATH, "common.json")
    if os.path.exists(common_path):
        try:
            with open(common_path, "r") as common_f:
                COMMON = json.load(common_f)
                common_f.close()
            log.info(f"Loaded common settings from {common_path}")
            ## verify connection & start TFM
            STAR_IP = COMMON.get("conn", None)
            STAR_U = COMMON.get("conn_u", None)
            STAR_P = COMMON.get("conn_p", None)
            if TFM.conn_ip != STAR_IP:
                # connection IP has changed, drop active TFM connection and restart with new IP address
                log.info(f"Updating TelFTPMan connection with new connection information.")
                TFM.disconnect()
                TFM.conn_ip = STAR_IP
                TFM.conn_u = STAR_U
                TFM.conn_p = STAR_P
                TFM.config_ok = True # i am not going to change TFM2's code rn so this is a hijack
                TFM.connect(ftp=False)
        except json.JSONDecodeError:
            log.error(f"Malformed JSON in {common_path}.")
        except: 
            log.error(f"Unhandled exception attempting to access {common_path}.", exc_info=True)

def cancel(pres_id:str=None, **kwargs):
    '''Cancels the active presentation and removes a loaded pres_id from the bank, if provided.'''
    # since this is the XL, we don't need (can't, really) to cancel a flavor, so we'll just delete it from our internal presentation bank
    global COMMON
    sensor_flavor = COMMON.get("sensor_flavor", "SN")
    global PRESENTATIONS
    ## delete loaded from bank if a not-yet-running presentation is cancelled before it's run
    if pres_id:
        if PRESENTATIONS.get(pres_id, None) == sensor_flavor:
            # this is a sensor flavor presentation, we need to call sensor down
            log.info(f"Dropping LDL presentation on Weather Star.")
            TFM.TN.write(f"echo \"CALL PE SNDN\" | /twc/bin/fire_str", timeout=10)
    if pres_id:
        if PRESENTATIONS.get(pres_id, None) != None: # only try to pop if loaded into bank (not run yet)
            PRESENTATIONS.pop(pres_id) # popper
            log.info(f"Presentation {pres_id} was cancelled.")

def load(pres_id:str, flav_name:str, flav_length:float, **kwargs):
    '''Load a presentation into the bank, in preparation for run.'''
    # First, let's try to derive an alias for the provided flav_name
    global COMMON
    # In common.json, you can define an alias name for a flavor. For example, 4comm will have "LDL1" and "LDL2" which we can map to different flavors specific to the jrencoder.
    aliases = COMMON.get("flavor_alias", {})
    alias = aliases.get(flav_name, None)
    if alias:
        log.debug(f"Called flavor '{flav_name}' has an alias of '{alias}'")
        flav_name = alias # flav_name is what will be used

    if flav_name:
        global PRESENTATIONS
        PRESENTATIONS[pres_id] = flav_name # set this before figuring out if flavor or sensor
        sensor_flavor = COMMON.get("sensor_flavor", "SN")
        if flav_name == sensor_flavor: # is sensor?
            log.debug(f"Got a load for sensor flavor. Sensor is cued in real-time, load not needed.")
            return # exit
        # if this isn't a sensor flavor then we'll try to load it
        TFM.TN.write(f"echo \"CALL PE LOAD FCST {flav_name}\" | /twc/bin/fire_str", timeout=10)
        log.info(f"Presentation {pres_id} loaded as flavor '{flav_name}'")

def run(pres_id:str, ts:float=0, **kwargs):
    '''Run a loaded presentation at the defined epoch timestamp. If undefined, run immediately.'''
    global COMMON
    sensor_flavor = COMMON.get("sensor_flavor", "SN")
    ts_offset = float(COMMON.get("ts_offset", 0))
    ts = ts + ts_offset # use an addition equation here, so a user defining a negative offset will subtract
    global PRESENTATIONS
    flavor = PRESENTATIONS.get(pres_id, None)
    log.debug(f"Desired run time: {ts}")
    retry_count = 0
    if not flavor:
        # if for some reason the RUN is sent faster than the LOAD, we can retry up to 5 times
        while not flavor and retry_count < 5: 
            log.warning(f"No flavor loaded matching ID {pres_id}! Trying again... ({retry_count + 1})")
            flavor = PRESENTATIONS.get(pres_id, None)
            retry_count += 1
            time.sleep(0.25)

    if flavor:
        # need to wait till the timestamp on our end before we can send
        while time.time() < ts:
            time.sleep(0.05) # spare the CPU cycles just a smidge...
        if flavor == sensor_flavor: 
            # run real-time sensor flavor
            log.info("Raising LDL presentation on Weather Star.")
            TFM.TN.write(f"echo \"CALL PE SNUP\" | /twc/bin/fire_str", timeout=10)
            # we don't pop the LDL pres from the bank because we need to remember it so we can cancel it later!
        else:
            # run loaded flavor
            TFM.TN.write(f"echo \"CALL PE RUN FCST {flavor}\" | /twc/bin/fire_str", timeout=10)
            PRESENTATIONS.pop(pres_id) # clear the presentation from the bank so it isn't re-run if the same ID happens to be called
    else:
        log.warning(f"Failed to run {pres_id}, no flavor loaded matching the ID.")
        



if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(level="DEBUG")
    load_settings()
    #cancel(pres_id=1)
    load(pres_id=1,flav_name="K",flav_length=120)
    #load(pres_id="LDL1",flav_name="LDL1")
    time.sleep(4)
    run(pres_id=1,ts=0)
    time.sleep(4)
    cancel(pres_id=1)