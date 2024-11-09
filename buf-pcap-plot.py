from scapy.all import rdpcap, TCP, IP, PPP
import matplotlib.pyplot as plt
import os

def parse_pcap(file_path, sender_ip, receiver_ip):
    sent_times = []
    sent_seqs = []
    ack_times = []
    ack_acks = []

    packets = rdpcap(file_path)

    for pkt in packets:
        try:
            # Check if the packet has PPP layer
            if PPP in pkt:
                ip_pkt = pkt[PPP][IP]
            elif IP in pkt:
                ip_pkt = pkt[IP]
            else:
                continue

            if TCP not in ip_pkt:
                continue

            tcp_pkt = ip_pkt[TCP]

            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst

            # Check if packet is s->r
            if src_ip == sender_ip and dst_ip == receiver_ip:
                # Extract SEQ
                sent_times.append(pkt.time)
                sent_seqs.append(tcp_pkt.seq)
            # Check if packet is r->s
            elif src_ip == receiver_ip and dst_ip == sender_ip:
                # Extract ACK
                ack_times.append(pkt.time)
                ack_acks.append(tcp_pkt.ack)
        except Exception as e:
            # Optionally, you can print the exception for debugging
            # print(f"Error parsing packet: {e}")
            continue

    return sent_times, sent_seqs, ack_times, ack_acks

def parse_buffer_log(buffer_log_file):
    buffer_times = []
    buffer_lengths = []
    with open(buffer_log_file, 'r') as f:
        # Assuming the buffer file has two columns: timestamp_ms and buffer_length_packets
        next(f)  # Skip header line, if any
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 2:
                continue
            timestamp_sec = float(parts[0])
            buffer_length_packets = int(parts[1])
            buffer_times.append(timestamp_sec)
            buffer_lengths.append(buffer_length_packets)
    return buffer_times, buffer_lengths

def parse_drop_log(drop_log_file):
    drop_times = []
    drop_seqs = []
    with open(drop_log_file, 'r') as f:
        next(f)  # Skip header line, if any
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue
            timestamp_sec = float(parts[0])
            seq_num = int(parts[1])
            drop_times.append(timestamp_sec)
            drop_seqs.append(seq_num)
    return drop_times, drop_seqs

def plot_seq_ack_buffer(sent_times, sent_seqs, ack_times, ack_acks, buffer_times, buffer_lengths, drop_times, drop_seqs, plot_title):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot SEQ and ACKs
    ax1.scatter(sent_times, sent_seqs, s=0.1, color='blue', label='Sent Seq')
    ax1.scatter(ack_times, ack_acks, s=0.05, alpha=0.4, color='red', label='ACKs')
    ax1.scatter(drop_times, drop_seqs, s=50, marker='x', color='black', label='Drops')

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Sequence / Acknowledgment Number')
    ax1.tick_params(axis='y')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(buffer_times, buffer_lengths, color='green', label='Buffer Length (packets)', alpha=0.4)

    ax2.set_ylabel('Buffer Length (packets)', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

    plt.title(plot_title)
    plt.show()

def main():
    pcap_file = 'CD-bw1p5Mb-dlay100-b450p.pcap'
    buffer_log_file = 'CD-bw1p5Mb-dlay100-b450p-buf.tr'
    drop_log_file = 'CD-bw1p5Mb-dlay100-b450p-drp.tr'

    sender_ip = '10.0.1.1'
    receiver_ip = '10.0.2.2'

    # Parse pcap, buffer length, and drop events
    sent_times, sent_seqs, ack_times, ack_acks = parse_pcap(pcap_file, sender_ip, receiver_ip)
    buffer_times, buffer_lengths = parse_buffer_log(buffer_log_file)
    drop_times, drop_seqs = parse_drop_log(drop_log_file)

    # Align the timestamps
    all_times = sent_times + ack_times + buffer_times + drop_times
    if not all_times:
        print("No data found.")
        return
    start_time = min(all_times)
    sent_times = [t - start_time for t in sent_times]
    ack_times = [t - start_time for t in ack_times]
    buffer_times = [t - start_time for t in buffer_times]
    drop_times = [t - start_time for t in drop_times]

    # Align SEQ to 0
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

    if drop_seqs:
        drop_seqs = [s - start_seq for s in drop_seqs]
    else:
        print("No drops found.")
        # Continue without drops if necessary

    base_name = os.path.basename(pcap_file)
    plot_title = os.path.splitext(base_name)[0]
    plot_seq_ack_buffer(sent_times, sent_seqs, ack_times, ack_acks, buffer_times, buffer_lengths, drop_times, drop_seqs, plot_title)

if __name__ == '__main__':
    main()

