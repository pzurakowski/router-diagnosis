import subprocess
import time
from flask import Flask, jsonify, render_template
from collections import deque

app = Flask(__name__)

router_data = deque()
last_failed_timestamp = None

TWO_HOURS_IN_SECONDS = 2 * 60 * 60

def ping_host(host):
    try:
        output = subprocess.check_output(['ping', '-c', '1', host])
        return True, float(output.decode('utf-8').split('time=')[1].split(' ')[0])
    except subprocess.CalledProcessError:
        return False, None

def get_channel():
    try:
        output = subprocess.check_output(['iwlist', 'wlp1s0', 'channel'])
        channel_line = [line for line in output.decode('utf-8').split('\n') if 'Current' in line][0]
        channel = int(channel_line.split(' ')[-1].split(')')[0])
        return channel
    except subprocess.CalledProcessError:
        return None

def collect_router_data():
    global last_failed_timestamp
    while True:
        ping_success_1, ping_time_1 = ping_host('1.1.1.1')
        ping_success_2, ping_time_2 = ping_host('192.168.0.1')
        channel = get_channel()

        current_time = time.time()
        if not ping_success_1 or not ping_success_2:
            last_failed_timestamp = current_time

        router_data.append({
            'timestamp': current_time,
            'ping_1': {'success': ping_success_1, 'time_ms': ping_time_1},
            'ping_2': {'success': ping_success_2, 'time_ms': ping_time_2},
            'wifi_channel': channel
        })

        if(len(router_data) > TWO_HOURS_IN_SECONDS):
            router_data.popleft()

        time.sleep(1)

@app.route('/')
def home():
    last_result = router_data[-1] if router_data else None
    return render_template('index.html', last_result=last_result, last_failed_timestamp=last_failed_timestamp, router_data=router_data)

@app.route('/export')
def export_data():
    return jsonify(router_data)

if __name__ == '__main__':
    import threading
    threading.Thread(target=collect_router_data, daemon=True).start()
    app.run(debug=True)

