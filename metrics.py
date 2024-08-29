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

# Дополнительные метрики
mytoncore_status_metric = Info('myton_mytoncore_status', 'Status of Mytoncore', registry=registry)
mytoncore_uptime_metric = Gauge('myton_mytoncore_uptime', 'Uptime of Mytoncore in seconds', registry=registry)
local_validator_status_metric = Info('myton_local_validator_status', 'Status of Local Validator', registry=registry)
local_validator_uptime_metric = Gauge('myton_local_validator_uptime', 'Uptime of Local Validator in seconds', registry=registry)
local_validator_out_of_sync_metric = Gauge('myton_local_validator_out_of_sync', 'Local validator out of sync in seconds', registry=registry)
local_validator_last_state_serialization_metric = Gauge('myton_local_validator_last_state_serialization', 'Blocks since last state serialization', registry=registry)
local_validator_database_size_metric = Gauge('myton_local_validator_database_size', 'Local validator database size in GB', registry=registry)
version_mytonctrl_metric = Info('myton_version_mytonctrl', 'Version of MyTonCtrl', registry=registry)
version_validator_metric = Info('myton_version_validator', 'Version of Validator', registry=registry)
network_info_metric = Info('myton_network_info', 'Network name', registry=registry)
election_status_info_metric = Info('myton_election_status', 'Election status', registry=registry)
adnl_address_info_metric = Info('myton_adnl_address', 'ADNL address of the local validator', registry=registry)
public_adnl_address_info_metric = Info('myton_public_adnl_address', 'Public ADNL address of node', registry=registry)
wallet_address_info_metric = Info('myton_wallet_address', 'Local validator wallet address', registry=registry)

# Регулярное выражение для удаления управляющих символов ANSI
ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def parse_uptime(uptime_str):
    """Парсинг строки времени работы и преобразование в секунды."""
    time_value, unit = uptime_str.split()
    time_value = int(time_value)
    if 'day' in unit:
        return time_value * 86400  # Конвертация дней в секунды
    elif 'hour' in unit:
        return time_value * 3600  # Конвертация часов в секунды
    elif 'minute' in unit:
        return time_value * 60  # Конвертация минут в секунды
    else:
        return time_value  # Предполагаем, что это уже секунды

def collect_metrics():
    # Выполняем команду и получаем её вывод
    output = subprocess.getoutput("echo 'status' | mytonctrl")

    # Удаляем управляющие символы ANSI
    output = ansi_escape.sub('', output)

    # Парсинг вывода
    validator_index = -1
    online_validators = -100
    all_validators = -100
    local_wallet_balance = 0

    # По умолчанию значения меток пустые
    network_name = "unknown"
    election_status = "unknown"
    adnl_address = "unknown"
    public_adnl_address = "unknown"
    wallet_address = "unknown"
    mytoncore_status = "unknown"
    mytoncore_uptime = -100
    local_validator_status = "unknown"
    local_validator_uptime = -100
    local_validator_out_of_sync = -100
    local_validator_last_state_serialization = -100
    local_validator_database_size = -100
    version_mytonctrl = "unknown"
    version_validator = "unknown"

    for line in output.splitlines():
        if 'Validator index:' in line:
            try:
                validator_index = int(line.split(':')[-1].strip())
            except ValueError:
                validator_index = -100
        elif 'Number of validators:' in line:
            numbers = line.split(':')[-1].strip()
            try:
                online_validators = int(numbers.split('(')[0].strip())
            except ValueError:
                online_validators = -100
            try:
                all_validators = int(numbers.split('(')[1].replace(')', '').strip())
            except ValueError:
                all_validators = -100
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
                local_wallet_balance = -100
        elif 'Mytoncore status:' in line:
            parts = line.split(':')[-1].strip().split(',')
            mytoncore_status = parts[0].strip()
            if len(parts) > 1:
                mytoncore_uptime = parse_uptime(parts[1].strip())
        elif 'Local validator status:' in line:
            parts = line.split(':')[-1].strip().split(',')
            local_validator_status = parts[0].strip()
            if len(parts) > 1:
                local_validator_uptime = parse_uptime(parts[1].strip())
        elif 'Local validator out of sync:' in line:
            try:
                local_validator_out_of_sync = int(line.split(':')[-1].strip().split()[0])
            except ValueError:
                local_validator_out_of_sync = -100
        elif 'Local validator last state serialization:' in line:
            try:
                local_validator_last_state_serialization = int(line.split(':')[-1].strip().split()[0])
            except ValueError:
                local_validator_last_state_serialization = -100
        elif 'Local validator database size:' in line:
            try:
                local_validator_database_size = float(line.split(':')[-1].strip().split()[0])
            except ValueError:
                local_validator_database_size = -100
        elif 'Version mytonctrl:' in line:
            version_mytonctrl = line.split(':')[-1].strip()
        elif 'Version validator:' in line:
            version_validator = line.split(':')[-1].strip()

    # Устанавливаем значения метрик
    validator_index_metric.set(validator_index)
    online_validators_metric.set(online_validators)
    all_validators_metric.set(all_validators)
    local_wallet_balance_metric.set(local_wallet_balance)
    local_validator_out_of_sync_metric.set(local_validator_out_of_sync)
    local_validator_last_state_serialization_metric.set(local_validator_last_state_serialization)
    local_validator_database_size_metric.set(local_validator_database_size)
    mytoncore_uptime_metric.set(mytoncore_uptime)
    local_validator_uptime_metric.set(local_validator_uptime)

    # Устанавливаем значения меток
    network_info_metric.info({'name': network_name})
    election_status_info_metric.info({'status': election_status})
    adnl_address_info_metric.info({'address': adnl_address})
    public_adnl_address_info_metric.info({'address': public_adnl_address})
    wallet_address_info_metric.info({'address': wallet_address})
    mytoncore_status_metric.info({'status': mytoncore_status})
    local_validator_status_metric.info({'status': local_validator_status})
    version_mytonctrl_metric.info({'version': version_mytonctrl})
    version_validator_metric.info({'version': version_validator})

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