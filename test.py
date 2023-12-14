import time

import yaml
from apscheduler.schedulers.background import BackgroundScheduler

config_scheduler = None

def load_config():
    global config_scheduler
    with open('config/scheduler_config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        config_scheduler = config['settings']['scheduler']
        # Add your logic to use the reloaded config_scheduler here
        # print("Config reloaded:", config_scheduler)

# Create an instance of BackgroundScheduler
scheduler = BackgroundScheduler()

# Add a job to the scheduler that reloads the configuration every 5 seconds (adjust the interval as needed)
scheduler.add_job(load_config, 'interval', seconds=5)

# Start the scheduler
scheduler.start()

# Keep the program running
try:
    while True:
        # Use the config_scheduler object within the loop as needed
        if config_scheduler:
            print("Using config_scheduler:", config_scheduler)
        time.sleep(500)
except (KeyboardInterrupt, SystemExit):
    # Shut down the scheduler gracefully
    scheduler.shutdown()
