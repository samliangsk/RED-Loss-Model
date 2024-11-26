from scapy.all import rdpcap, TCP, IP
import matplotlib.pyplot as plt

def parse_persistent_pcap(file_path, sender_ip, receiver_ip, dest_port):
    sent_times = []
    sent_seqs = []

    packets = rdpcap(file_path)

    for pkt in packets:
        try:
            if IP in pkt and TCP in pkt:
                ip_pkt = pkt[IP]
                tcp_pkt = ip_pkt[TCP]

                src_ip = ip_pkt.src
                dst_ip = ip_pkt.dst
                src_port = tcp_pkt.sport
                dst_port_pkt = tcp_pkt.dport

                # Check if packet is s->r and matches dest_port
                if src_ip == sender_ip and dst_ip == receiver_ip and dst_port_pkt == dest_port:
                    # Extract SEQ
                    sent_times.append(pkt.time)
                    sent_seqs.append(tcp_pkt.seq)
        except Exception as e:
            print("Error in parse persistent pcap:", e)
            continue
            
    return sent_times, sent_seqs

def parse_bursty_pcap(file_path):
    # Returns a dictionary mapping from dest_port to list of packet times
    flow_packet_times = {}

    packets = rdpcap(file_path)

    for pkt in packets:
        try:
            if IP in pkt and TCP in pkt:
                ip_pkt = pkt[IP]
                tcp_pkt = ip_pkt[TCP]

                dst_port_pkt = tcp_pkt.dport

                # Collect packet times based on destination port
                if dst_port_pkt not in flow_packet_times:
                    flow_packet_times[dst_port_pkt] = []
                flow_packet_times[dst_port_pkt].append(pkt.time)
        except Exception as e:
            print("Error in parse bursty pcap:", e)
            continue

    return flow_packet_times

def identify_on_off_periods(flow_packet_times, off_threshold=0.1):
    # off_threshold is in seconds
    flow_on_periods = {}

    for dest_port, times in flow_packet_times.items():
        times.sort()
        on_periods = []
        if not times:
            continue

        start_time = times[0]
        last_time = times[0]

        for i in range(1, len(times)):
            delta_t = times[i] - last_time
            if delta_t > off_threshold:
                # End of current "On" period
                end_time = last_time
                on_periods.append((start_time, end_time))
                # Start a new "On" period
                start_time = times[i]
            last_time = times[i]

        # Add the last "On" period
        on_periods.append((start_time, last_time))
        flow_on_periods[dest_port] = on_periods

    return flow_on_periods

def build_bursty_flow_events(flow_on_periods):
    # Returns a list of events: (time, delta_active_flows)
    events = []
    for dest_port, periods in flow_on_periods.items():
        for start_time, end_time in periods:
            events.append((start_time, +1))
            events.append((end_time, -1))
    # Sort events by time
    events.sort(key=lambda x: x[0])
    return events

def build_active_flows_time_series(events):
    # Returns lists of times and active_counts suitable for step plotting
    times = []
    active_counts = []
    current_active = 0

    if not events:
        return [], []

    for event in events:
        time, delta = event

        if times and time == times[-1]:
            # Same timestamp, update active_counts
            current_active += delta
            active_counts[-1] = current_active
        else:
            # Add previous state
            if times:
                times.append(time)
                active_counts.append(current_active)
            # Update state
            current_active += delta
            times.append(time)
            active_counts.append(current_active)

    return times, active_counts

def parse_drop_log(drop_log_file, persistent_flow_port):
    drop_times = []
    drop_seqs = []
    with open(drop_log_file, 'r') as f:
        next(f)  # Skip header line, if any
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue
            timestamp_sec = float(parts[0])
            seq_num = int(parts[1])
            dest_port = int(parts[2])
            if dest_port == persistent_flow_port:
                drop_times.append(timestamp_sec)
                drop_seqs.append(seq_num)
    return drop_times, drop_seqs

def plot_persistent_flow_with_bursty(sent_times, sent_seqs, drop_times, drop_seqs, bursty_times, active_counts, plot_title):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot sent sequences
    ax1.scatter(sent_times, sent_seqs, s=0.5, color='blue', label='Persistent Flow Sent Sequences')

    # Plot drops
    ax1.scatter(drop_times, drop_seqs, s=50, color='red', label='Drops', marker='x')

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Sequence Number')
    ax1.tick_params(axis='y')
    ax1.grid(True)

    # Plot number of active bursty flows
    ax2 = ax1.twinx()
    ax2.step(bursty_times, active_counts, where='post', color='green', label='Active Bursty Flows', alpha=0.5)

    ax2.set_ylabel('Number of Active Bursty Flows', color='green')
    ax2.tick_params(axis='y', labelcolor='green')

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

    plt.title(plot_title)
    plt.show()

def main():
    persistent_pcap_file = 'CD-bursty-1-1.pcap'  # Replace with your actual persistent flow pcap file
    bursty_pcap_file = 'CD-bursty-2-1.pcap'  # Replace with your actual bursty flows pcap file
    drop_log_file = 'CD-bursty-drp.tr'  # Replace with your actual drop log file

    # Adjust these IPs and port as per your setup
    sender_ip = '10.0.1.1'  # Persistent flow sender IP
    receiver_ip = '10.0.3.2'  # Receiver IP
    persistent_flow_port = 50000  # Port for persistent flow

    # Parse persistent flow pcap
    sent_times, sent_seqs = parse_persistent_pcap(persistent_pcap_file, sender_ip, receiver_ip, persistent_flow_port)

    # Parse bursty flows pcap and identify On periods
    flow_packet_times = parse_bursty_pcap(bursty_pcap_file)
    flow_on_periods = identify_on_off_periods(flow_packet_times, off_threshold=0.1)
    events = build_bursty_flow_events(flow_on_periods)
    bursty_times, active_counts = build_active_flows_time_series(events)

    # Parse drop log
    drop_times, drop_seqs = parse_drop_log(drop_log_file, persistent_flow_port)

    # Adjust times to align
    all_times = sent_times + drop_times + bursty_times

    if not all_times:
        print("No data found.")
        return
    start_time = min(all_times)

    sent_times = [t - start_time for t in sent_times]
    drop_times = [t - start_time for t in drop_times]
    bursty_times = [t - start_time for t in bursty_times]

    if sent_seqs:
        start_seq = sent_seqs[0]
        sent_seqs = [s - start_seq for s in sent_seqs]
    else:
        sent_seqs = []

    if drop_seqs:
        drop_seqs = [s - start_seq for s in drop_seqs]
    else:
        drop_seqs = []

    # Plot
    plot_title = "Persistent Flow with Active Bursty Flows"
    plot_persistent_flow_with_bursty(sent_times, sent_seqs, drop_times, drop_seqs, bursty_times, active_counts, plot_title)

if __name__ == '__main__':
    main()
