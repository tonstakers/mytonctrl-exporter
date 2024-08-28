import subprocess
import re
import os
from prometheus_client import start_http_server, Gauge, generate_latest, Info
from prometheus_client.core import CollectorRegistry
from http.server import BaseHTTPRequestHandler, HTTPServer

# Создаем метрики с префиксом myton_
registry = CollectorRegistry()
validator_index_metric = Gauge('myton_validator_index', 'Index of the local validator', registry=registry)
online_validators_metric = Gauge('myton_online_validators', 'Number of online validators', registry=registry)
all_validators_metric = Gauge('myton_all_validators', 'Total number of validators', registry=registry)
local_wallet_balance_metric = Gauge('myton_local_validator_wallet_balance', 'Balance of the local validator wallet', registry=registry)

# Метрики с метками (labels)
network_info = Info('myton_network_info', 'Network name', registry=registry)
election_status_info = Info('myton_election_status', 'Election status', registry=registry)
adnl_address_info = Info('myton_adnl_address', 'ADNL address of the local validator', registry=registry)
public_adnl_address_info = Info('myton_public_adnl_address', 'Public ADNL address of node', registry=registry)
wallet_address_info = Info('myton_wallet_address', 'Local validator wallet address', registry=registry)

# Регулярное выражение для удаления управляющих символов ANSI
ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def collect_metrics():
    # Выполняем команду и получаем её вывод
    output = subprocess.getoutput("echo 'status' | mytonctrl")

    # Удаляем управляющие символы ANSI
    output = ansi_escape.sub('', output)

    # Парсинг вывода
    validator_index = -1
    online_validators = 0
    all_validators = 0
    local_wallet_balance = 0

    # По умолчанию значения меток пустые
    network_name = "unknown"
    election_status = "unknown"
    adnl_address = "unknown"
    public_adnl_address = "unknown"
    wallet_address = "unknown"

    for line in output.splitlines():
        if 'Validator index:' in line:
            try:
                validator_index = int(line.split(':')[-1].strip())
            except ValueError:
                validator_index = -100  # Устанавливаем значение по умолчанию, если не удается преобразовать
        elif 'Number of validators:' in line:
            numbers = line.split(':')[-1].strip()
            try:
                online_validators = int(numbers.split('(')[0].strip())
            except ValueError:
                online_validators = 0  # Устанавливаем значение по умолчанию
            try:
                all_validators = int(numbers.split('(')[1].replace(')', '').strip())
            except ValueError:
                all_validators = 0  # Устанавливаем значение по умолчанию
        elif 'Network name:' in line:
            network_name = line.split(':')[-1].strip()
        elif 'Election status:' in line:
            election_status = line.split(':')[-1].strip()
        elif 'ADNL address of local validator:' in line:
            adnl_address = line.split(':')[-1].strip()
        elif 'Public ADNL address of node:' in line:
            public_adnl_address = line.split(':')[-1].strip()
        elif 'Local validator wallet address:' in line:
            wallet_address = line.split(':')[-1].strip()
        elif 'Local validator wallet balance:' in line:
            try:
                local_wallet_balance = float(line.split(':')[-1].strip())
            except ValueError:
                local_wallet_balance = -100  # Устанавливаем значение по умолчанию

    # Устанавливаем значения метрик
    validator_index_metric.set(validator_index)
    online_validators_metric.set(online_validators)
    all_validators_metric.set(all_validators)
    local_wallet_balance_metric.set(local_wallet_balance)

    # Устанавливаем значения меток
    network_info.info({'name': network_name})
    election_status_info.info({'status': election_status})
    adnl_address_info.info({'address': adnl_address})
    public_adnl_address_info.info({'address': public_adnl_address})
    wallet_address_info.info({'address': wallet_address})

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            collect_metrics()
            self.send_response(200)
            self.send_header("Content-type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            output = generate_latest(registry)
            self.wfile.write(output)
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=MyHandler):
    # Порт и адрес берутся из переменных окружения или используются значения по умолчанию
    port = int(os.getenv('MTCRL_EXPORTER_PORT', '9140'))
    bind_addr = os.getenv('MTCRL_EXPORTER_BIND_ADDR', '')

    server_address = (bind_addr, port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd server on {bind_addr} port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()