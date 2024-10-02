import subprocess
import time

# code referencing https://github.com/mininet/mininet-tests/blob/master/buffersizing/buffersizing.py

def monitor_queue(iface='router-eth2', output_file='./queue_log.txt', interval=0.05):
    """
    Monitor the queue length of a network interface.

    Args:
        iface (str): Network interface to monitor (e.g., 'router-eth2').
        output_file (str): Path to the output log file.
        interval (float): Time interval between samples in seconds.
    """
    with open(output_file, 'w') as f:
        f.write('timestamp_ms\tqueue_length_bytes\n')
        try:
            while True:
                cmd = ['tc', '-s', 'qdisc', 'show', 'dev', iface]
                output = subprocess.check_output(cmd).decode('utf-8')

                qlen_bytes = parse_queue_length(output)
                # drop = parse_drop(output)
                timestamp_ms = int(time.time() * 1000)

                f.write(f'{timestamp_ms}\t{qlen_bytes}\n')
                f.flush()

                time.sleep(interval)
        except Exception as e:
            print(f"Queue monitor stopped: {e}")

def parse_queue_length(tc_output):
    """
    Parse the 'tc' command output to extract the queue length in bytes.

    Args:
        tc_output (str): Output from 'tc -s qdisc show dev <iface>'.

    Returns:
        int: Queue length in bytes.
    """
    qlen_bytes = 0
    lines = tc_output.split('\n')
    for line in lines:
        line = line.strip()
        if 'backlog' in line:
            tokens = line.split()
            try:
                idx = tokens.index('backlog')
                qlen_str = tokens[idx + 1]
                if qlen_str.endswith('b'):
                    qlen_bytes = int(qlen_str[:-1])  # Remove 'b' and convert to int
                elif qlen_str.endswith('Kb'):
                    qlen_bytes = int(float(qlen_str[:-2]) * 1024)  # Convert Kb to bytes
                elif qlen_str.endswith('Mb'):
                    qlen_bytes = int(float(qlen_str[:-2]) * 1024 * 1024)  # Convert Mb to bytes
            except (ValueError, IndexError):
                pass
            break
    return qlen_bytes

# def parse_drop(tc_output):
#     """
#     Parse the 'tc' command output to extract the queue length in bytes.

#     Args:
#         tc_output (str): Output from 'tc -s qdisc show dev <iface>'.

#     Returns:
#         int: Queue length in bytes.
#     """
#     drop = 0
#     lines = tc_output.split('\n')
#     for line in lines:
#         line = line.strip()
#         if 'drop' in line:
#             tokens = line.split()
#             try:
#                 idx = tokens.index('drop')
#                 drop_str = tokens[idx + 1]
#                 drop = int(drop_str)
#             except (ValueError, IndexError):
#                 pass
#             break
#     return drop



def main():
    monitor_queue()

if __name__ == '__main__':
    main()