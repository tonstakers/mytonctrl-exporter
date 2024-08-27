import subprocess
import re
from prometheus_client import start_http_server, Gauge

# Create metrics with the prefix myton_
validator_index_metric = Gauge('myton_validator_index', 'Index of the local validator')
online_validators_metric = Gauge('myton_online_validators', 'Number of online validators')
all_validators_metric = Gauge('myton_all_validators', 'Total number of validators')

# Regular expression to remove ANSI control characters
ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def collect_metrics():
    # Execute the command and get its output
    output = subprocess.getoutput("echo 'status' | mytonctrl")

    # Remove ANSI control characters
    output = ansi_escape.sub('', output)

    # Parse the output
    validator_index = -1
    online_validators = 0
    all_validators = 0

    for line in output.splitlines():
        if 'Validator index:' in line:
            validator_index = int(line.split(':')[-1].strip())
        elif 'Number of validators:' in line:
            numbers = line.split(':')[-1].strip()
            online_validators = int(numbers.split('(')[0].strip())
            all_validators = int(numbers.split('(')[1].replace(')', '').strip())

    # Set the metric values
    validator_index_metric.set(validator_index)
    online_validators_metric.set(online_validators)
    all_validators_metric.set(all_validators)

if __name__ == "__main__":
    # Start the HTTP server on port 8000
    start_http_server(8000)

    # Periodically collect and update metrics
    while True:
        collect_metrics()