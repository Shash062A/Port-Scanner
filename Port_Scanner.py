import socket, threading
from datetime import datetime
import argparse
from queue import Queue

# ---------------- CLI ARGUMENTS ----------------
parser = argparse.ArgumentParser(description="Simple Port Scanner")
parser.add_argument("-t", "--target", help="Target host")
parser.add_argument("-s", "--start", type=int, default=0, help="Start port")
parser.add_argument("-e", "--end", type=int, default=1037, help="End port")
parser.add_argument("-d", "--delay", type=float, default=0.001, help="Timeout delay")
args = parser.parse_args()

try:
    host = "localhost"
    host = args.target if args.target else input("Enter The Host Name/IP Address To Scan: ")
    host_ip = socket.gethostbyname(host)

except socket.gaierror:
    print("Host couldn't be found")
    exit()

print(host)
print(host_ip)

threads = []
open_ports = {}
lock = threading.Lock()
scanned_ports = 0

# ----------- THREAD CONTROL (ADDED ONLY) -----------
MAX_THREADS = 100
port_queue = Queue()

# ---------------- COMMON SERVICE MAPPING ----------------
COMMON_SERVICES = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    8080: "HTTP-ALT"
}

def banner_grab(sock):
    try:
        sock.send(b"HELLO\r\n")
        banner = sock.recv(1024).decode(errors="ignore").strip()
        return banner
    except:
        return "No banner"

def check_ports(ip, port, delay, open_ports):
    global scanned_ports
    sock = None
    try:

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.settimeout(delay)
        result = sock.connect_ex((ip, port))

        if result == 0:
            service = COMMON_SERVICES.get(port, "Unknown")
            banner = banner_grab(sock)
            with lock:
                open_ports[port] = f"Open | Service: {service} | Banner: {banner}"

    except socket.gaierror:
        print("Couldn't Be Found Or Connect to Server")

    except socket.error:
        print("Socket Error Happened While Connecting To Server. May Host Is Down Or Refusing Connection. Try Again Later.")

    finally:
        if sock:
            sock.close()

    # -------- SCANNING PROGRESS --------
    with lock:
        scanned_ports += 1
        print(f"\rScanning progress: {scanned_ports}", end="")

# ----------- WORKER FUNCTION (ADDED ONLY) -----------
def worker(ip, delay, open_ports):
    while not port_queue.empty():
        port = port_queue.get()
        check_ports(ip, port, delay, open_ports)
        port_queue.task_done()

def scanning_ports(host_ip, delay, file_reference):

    # CREATE THREADS
    for port in range(args.start, args.end):
        port_queue.put(port)

    for _ in range(MAX_THREADS):
        thread = threading.Thread(
            target=worker,
            args=(host_ip, delay, open_ports)
        )
        threads.append(thread)
        # AF_INET = IPv4 
        # SOCK_STREAM = TCP 
        # AF_INET means IP4 address. AF_INET6 means IP^ address 
        # SOCK_STREAM means we are using TCP. SOCK_DGRAM for UDP

    # START THREADS
    for t in threads:
        t.start()

    # JOIN THREADS
    for t in threads:
        t.join()

    print("\nScan completed.")

    # WRITE RESULTS TO FILE
    for key in open_ports:
        file_reference.write("\nOpen port Number:" + str(key))
        file_reference.write(" | " + open_ports[key])


file_reference = open("Port-Scanner-062A.txt", "w")

# RUN SCAN
start_time = datetime.now()
print("Start Time: {}".format(start_time))
file_reference.write("Start Time: {}\n".format(start_time))

scanning_ports(host_ip, args.delay, file_reference)

end_time = datetime.now()
print("End Time: {}".format(end_time))
file_reference.write("\n\nEnd Time: {}\n".format(end_time))

total_time = end_time - start_time
print("Total Time: {}".format(total_time))
file_reference.write("\nTotal Time: {}\n".format(total_time))

# PRINT RESULTS
for key in open_ports:
    print("Open Port number:", key, "|", open_ports[key])

file_reference.close()
