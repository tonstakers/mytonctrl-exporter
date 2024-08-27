import subprocess
import re
import os
from prometheus_client import start_http_server, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
from http.server import BaseHTTPRequestHandler, HTTPServer

# Создаем метрики с префиксом myton_
registry = CollectorRegistry()
validator_index_metric = Gauge('myton_validator_index', 'Index of the local validator', registry=registry)
online_validators_metric = Gauge('myton_online_validators', 'Number of online validators', registry=registry)
all_validators_metric = Gauge('myton_all_validators', 'Total number of validators', registry=registry)

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

    # Устанавливаем значения метрик
    validator_index_metric.set(validator_index)
    online_validators_metric.set(online_validators)
    all_validators_metric.set(all_validators)

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