import pandas as pd
from scapy.all import rdpcap, TCP, IP

def extract_packets(pcap_file, src_ip, dst_ip):
    packets = rdpcap(pcap_file)
    packet_list = []

    for pkt in packets:
        if IP in pkt and TCP in pkt:
            if pkt[IP].src == src_ip and pkt[IP].dst == dst_ip:
                seq = pkt[TCP].seq
                ip_id = pkt[IP].id
                timestamp = pkt.time
                packet_list.append({
                    'seq': seq,
                    'ip_id': ip_id,
                    'timestamp': timestamp
                })

    return pd.DataFrame(packet_list)

def main():
    # Define IP addresses
    sender_ip = '10.0.1.1'   # IP of sender
    receiver_ip = '10.0.2.2' # IP of receiver

    # Extract packets sent from sender to receiver
    sender_packets = extract_packets('CD-bw1Mb-b45p.pcap', sender_ip, receiver_ip)

    # Read packet_drop file
    drop_df = pd.read_csv('CD-bw1Mb-b45p-drp.tr', header=None, names=['seq'])
    # Get drop counts for each sequence number
    drop_counts = drop_df['seq'].value_counts().to_dict()

    # Sort sender_packets by timestamp
    sender_packets = sender_packets.sort_values('timestamp').reset_index(drop=True)
    sender_packets['dropped'] = False

    # Copy drop_counts to avoid modifying the original
    current_drop_counts = drop_counts.copy()

    # Process packets to mark drops
    for idx, row in sender_packets.iterrows():
        seq = row['seq']
        if seq in current_drop_counts and current_drop_counts[seq] > 0:
            # Mark packet as dropped
            sender_packets.at[idx, 'dropped'] = True
            # Decrement drop count for this sequence number
            current_drop_counts[seq] -= 1

    # Calculate unconditional probability of drop
    P_uncond = sender_packets['dropped'].mean()

    # Calculate conditional probability of drop given previous packet was dropped
    sender_packets['prev_dropped'] = sender_packets['dropped'].shift(1).fillna(False)
    both_dropped = sender_packets['dropped'] & sender_packets['prev_dropped']
    N_prev_dropped = sender_packets['prev_dropped'].sum()
    N_both_dropped = both_dropped.sum()
    if N_prev_dropped > 0:
        P_cond = N_both_dropped / N_prev_dropped
    else:
        P_cond = 0

    print(f"Unconditional probability: {P_uncond:.4f}")
    print(f"Conditional probability: {P_cond:.4f}")

    # Optionally, save dropped packets to a CSV file
    # dropped_packets = sender_packets[sender_packets['dropped']]
    # dropped_packets.to_csv('dropped_packets.csv', index=False)

if __name__ == '__main__':
    main()
