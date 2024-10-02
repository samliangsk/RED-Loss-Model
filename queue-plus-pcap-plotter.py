import dpkt
import socket
import matplotlib.pyplot as plt

def parse_pcap(file_path, sender_ip, receiver_ip):
    sent_times = []
    sent_seqs = []
    ack_times = []
    ack_acks = []
    with open(file_path, 'rb') as f:
        pcap = dpkt.pcap.Reader(f)

        for timestamp, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                if not isinstance(eth.data, dpkt.ip.IP):
                    continue
                ip = eth.data
                if not isinstance(ip.data, dpkt.tcp.TCP):
                    continue
                tcp = ip.data

                src_ip = socket.inet_ntoa(ip.src)
                dst_ip = socket.inet_ntoa(ip.dst)

                # Check if packet is s->r
                if src_ip == sender_ip and dst_ip == receiver_ip:
                    # Extract SEQ
                    sent_times.append(timestamp)
                    sent_seqs.append(tcp.seq)
                # Check if packet is r->s
                elif src_ip == receiver_ip and dst_ip == sender_ip:
                    # Extract ACK
                    ack_times.append(timestamp)
                    ack_acks.append(tcp.ack)
            except Exception as e:
                continue

    return sent_times, sent_seqs, ack_times, ack_acks

def parse_queue_log(queue_log_file):
    queue_times = []
    queue_lengths = []
    with open(queue_log_file, 'r') as f:
        next(f)  # Skip header line
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 2:
                continue
            timestamp_ms = int(parts[0])
            queue_length_bytes = int(parts[1])
            timestamp_sec = timestamp_ms / 1000.0
            queue_times.append(timestamp_sec)
            queue_lengths.append(queue_length_bytes)
    return queue_times, queue_lengths

def plot_seq_ack_queue(sent_times, sent_seqs, ack_times, ack_acks, queue_times, queue_lengths):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot SEQ and ACKs
    ax1.scatter(sent_times, sent_seqs, s=.1, color='blue', label='Sent Seq')
    ax1.scatter(ack_times, ack_acks, s=.1, color='red', label='ACKs')

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Sequence / Acknowledgment Number')
    ax1.tick_params(axis='y')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(queue_times, queue_lengths, color='green', label='Queue Length (bytes)', alpha=0.4)

    ax2.set_ylabel('Queue Length (bytes)', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

    plt.title('TCP Sequence Numbers, ACKs, and Queue Length Over Time')
    plt.show()

def main():
    pcap_file = 'sender8-REDlimit12500prob0_1.pcap'
    queue_log_file = 'queue_log.txt'

    sender_ip = '10.0.1.1'
    receiver_ip = '10.0.3.1'

    # Parse pcap and queue length
    sent_times, sent_seqs, ack_times, ack_acks = parse_pcap(pcap_file, sender_ip, receiver_ip)
    queue_times, queue_lengths = parse_queue_log(queue_log_file)


    # Align the timestamps
    start_time = min(min(sent_times),min(ack_times),min(queue_times))
    sent_times = [t - start_time for t in sent_times]
    ack_times = [t - start_time for t in ack_times]
    queue_times = [t - start_time for t in queue_times]

    # Aligned SEQ to 0
    if sent_seqs:
        start_seq = sent_seqs[0]
        sent_seqs = [s - start_seq for s in sent_seqs]
    else:
        print("No sent sequences found.")
        return

    if ack_acks:
        ack_acks = [a - start_seq for a in ack_acks]
    else:
        print("No ACKs found.")
        return

    plot_seq_ack_queue(sent_times, sent_seqs, ack_times, ack_acks, queue_times, queue_lengths)

if __name__ == '__main__':
    main()
