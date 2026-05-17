import xlcontrol
from netrunner import receiver 
import asyncio, logging, coloredlogs, time

log = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

xlcontrol.load_settings()

receiver.SERVER_ADDRESS = xlcontrol.COMMON.get("netrunner", "http://localhost:4000") # get server add from config 

receiver.FUNCTIONS["LF_LOAD"] = xlcontrol.load
receiver.FUNCTIONS["LF_RUN"] = xlcontrol.run
receiver.FUNCTIONS["LF_CANCEL"] = xlcontrol.cancel

def refresh_configs(interval=120): # every 2 minutes by default
    while True:
        time.sleep(interval)
        log.info(f"Refreshing common.json.")
        xlcontrol.load_settings()

receiver.threading.Thread(target=refresh_configs, daemon=True).start() # wretched but idgaf

asyncio.run(receiver.main())