import machine
import network
import socket
import time


WIFI_SSID = ""
WIFI_PASSWORD = ""

MORSE_TIME_UNIT_MS = 200
MORSE_CONFIG = {
    'dit': 1,
    'dah': 3,
    'symbol': 1,
    'letter': 3,
    'word': 7
}
MAIN_PAGE = 'index.html'
MORSE_CODE = 'code.txt'
MORSE_CONFIG = {k: v*MORSE_TIME_UNIT_MS for k, v in MORSE_CONFIG.items()}

MAX_REQ_SIZE = 65536


class Server:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        self.led = machine.Pin('LED', machine.Pin.OUT)

        self.morse_code = self.morse_code_map()
        self.page = {}

    def start(self):
        try:
            connection = None
            ip = self.wifi_connect()
            connection = self.open_socket(ip)

            while True:
                self.serve(connection, ip)
        except Exception:
            if connection:
                connection.close()

    def wifi_connect(self):
        self.blink_led(100, 1)
        time.sleep_ms(1000)

        print()
        while True:
            print(f'Checking WiFi: {self.wlan.status()}')
            if self.wlan.status() == 3:
                break

            self.blink_led(100, 1)
            time.sleep_ms(500)

        print('Connected!')
        self.blink_led(100, 3)
        ip = self.wlan.ifconfig()[0]
        print(f'Open a browser to: http://{ip}')

        return ip

    def morse_blink_message(self, message):
        print(f'Sending message: {message}')
        words = message.split(' ')
        for word in words:
            for c in word:
                c = c.upper()

                try:
                    morse = self.morse_code[c]
                except KeyError:
                    continue

                print(f'{c}: {morse}')
                for token in morse:
                    if token == '.':
                        self.led.on()
                        time.sleep_ms(MORSE_CONFIG['dit'])
                        self.led.off()
                    elif token == '-':
                        self.led.on()
                        time.sleep_ms(MORSE_CONFIG['dah'])
                        self.led.off()

                    time.sleep_ms(MORSE_CONFIG['symbol'])

                time.sleep_ms(MORSE_CONFIG['letter'])

            time.sleep_ms(MORSE_CONFIG['word'])
            print()

        print('Message send\n')

    def blink_led(self, duration=1000, repeat=1):
        for _ in range(repeat+1):
            self.led.on()
            time.sleep_ms(duration)
            self.led.off()
            time.sleep_ms(duration)

    def morse_code_map(self):
        with open(MORSE_CODE) as fp:
            data = fp.read().strip().split('\n')

        code = {}
        for line in data:
            cols = line.split(' ')
            key = cols[0]
            value = cols[-1]
            code[key] = value

        return code

    def open_socket(self, ip):
        address = (ip, 80)

        connection = socket.socket()
        connection.bind(address)
        connection.listen(1)

        return connection

    def serve(self, connection, ip):
        page = self.load_page(ip)

        client = connection.accept()[0]
        request = client.recv(MAX_REQ_SIZE)
        request = str(request)

        try:
            path = request.split()[1]
        except IndexError:
            pass

        response = page
        if path == '/message':
            body = request.split('\\r\\n\\r\\n')

            message = ''
            if len(body) >= 2:
                message = body[1].strip("'")

            self.morse_blink_message(message)

            response = 'ok'

        client.send(response)
        client.close()

    def load_page(self, ip):
        if ip not in self.page:
            with open(MAIN_PAGE) as fp:
                self.page[ip] = fp.read().strip().replace('__SERVER_IP__', ip)

        return self.page[ip]


server = Server()
server.start()
