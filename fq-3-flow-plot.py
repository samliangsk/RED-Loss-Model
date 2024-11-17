from scapy.all import rdpcap, TCP, IP, PPP
import matplotlib.pyplot as plt
import os

# the 3 flow plotter that plots the buffer, and 3 flows

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
            print("Error in parse pcap")
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

def parse_buffer_log(buffer_log_file):
    buffer_times = []
    buffer_lengths = []
    with open(buffer_log_file, 'r') as f:
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
    drop_times = {}
    drop_seqs = {}
    with open(drop_log_file, 'r') as f:
        next(f)  # Skip header line, if any
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue
            timestamp_sec = float(parts[0])
            seq_num = int(parts[1])
            dest_port = int(parts[2])
            if dest_port not in drop_times:
                drop_times[dest_port] = []
                drop_seqs[dest_port] = []
            drop_times[dest_port].append(timestamp_sec)
            drop_seqs[dest_port].append(seq_num)
    return drop_times, drop_seqs

def plot_seq_ack_buffer(sent_times_list, sent_seqs_list, ack_times_list, ack_acks_list, buffer_times, buffer_lengths, drop_times_dict, drop_seqs_dict, flow_ports, plot_title):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    colors = ['blue', 'purple', 'red', 'gray', 'olive', 'cyan']

    num_flows = len(flow_ports)

    for idx in range(num_flows):
        color = colors[idx % len(colors)]
        
        port = flow_ports[idx]
        label_sent = f'Sent Seq Flow {port}'
        # label_ack = f'ACKs Flow {port}'
        label_drop = f'Drops Flow {port}'

        # Plot Sent Sequences
        
        ax1.scatter(sent_times_list[idx], sent_seqs_list[idx], s=0.5, color=color, label=label_sent)


        # Plot Drops
        if port in drop_times_dict:
            ax1.scatter(drop_times_dict[port], drop_seqs_dict[port], s=50, color=color, label=label_drop, marker='x')

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Sequence Number')
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
    pcap_files = ['CD-multiflow-1-1.pcap', 'CD-multiflow-2-1.pcap', 'CD-multiflow-3-1.pcap']  # Replace with your actual pcap file names
    buffer_log_file = 'CD-multiflow-buf.tr'
    drop_log_file = 'CD-multiflow-drp.tr'

    sender_ips = ['10.0.1.1', '10.0.2.1', '10.0.3.1']  # Adjust these IPs as per your setup
    receiver_ip = '10.0.4.2'  # Common receiver IP for all flows
    flow_ports = [50000, 50001, 50002]  # Ports for each flow

    sent_times_list = []
    sent_seqs_list = []
    ack_times_list = []
    ack_acks_list = []

    for idx, pcap_file in enumerate(pcap_files):
        sender_ip = sender_ips[idx]
        sent_times, sent_seqs, ack_times, ack_acks = parse_pcap(pcap_file, sender_ip, receiver_ip)
        sent_times_list.append(sent_times)
        sent_seqs_list.append(sent_seqs)
        ack_times_list.append(ack_times)
        ack_acks_list.append(ack_acks)

    # Parse buffer length and drop events
    buffer_times, buffer_lengths = parse_buffer_log(buffer_log_file)
    drop_times_dict, drop_seqs_dict = parse_drop_log(drop_log_file)

    # Align the timestamps
    all_times = []
    for times in sent_times_list:
        all_times.extend(times)
    for times in ack_times_list:
        all_times.extend(times)
    all_times.extend(buffer_times)
    for times in drop_times_dict.values():
        all_times.extend(times)

    if not all_times:
        print("No data found.")
        return
    start_time = min(all_times)

    # Adjust times and sequences per flow
    for idx in range(len(flow_ports)):
        sent_times_list[idx] = [t - start_time for t in sent_times_list[idx]]
        ack_times_list[idx] = [t - start_time for t in ack_times_list[idx]]

        

        if sent_seqs_list[idx]:
            start_seq = sent_seqs_list[idx][0]
            sent_seqs_list[idx] = [s - start_seq for s in sent_seqs_list[idx]]
        else:
            print(f"No sent sequences found for flow {flow_ports[idx]}.")
            sent_seqs_list[idx] = []

        if ack_acks_list[idx]:
            ack_acks_list[idx] = [a - start_seq for a in ack_acks_list[idx]]
        else:
            print(f"No ACKs found for flow {flow_ports[idx]}.")
            ack_acks_list[idx] = []

        # Adjust drop sequences
        port = flow_ports[idx]
        if port in drop_times_dict:
            drop_times_dict[port] = [t - start_time for t in drop_times_dict[port]]
            drop_seqs_dict[port] = [s - start_seq for s in drop_seqs_dict[port]]

    # Adjust buffer times
    buffer_times = [t - start_time for t in buffer_times]

    plot_title = "TCP Flows with Buffer and Drops"
    plot_seq_ack_buffer(sent_times_list, sent_seqs_list, ack_times_list, ack_acks_list, buffer_times, buffer_lengths, drop_times_dict, drop_seqs_dict, flow_ports, plot_title)

if __name__ == '__main__':
    main()
