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
    sender_ip = '10.0.1.1'   # IP of sender1
    receiver_ip = '10.0.2.2' # IP of receiver

    # Extract packets sent from sender1 to receiver
    sender_packets = extract_packets('DT10000Sender5BDP.pcap', sender_ip, receiver_ip)

    # Extract packets received at router2 from sender1
    router_packets = extract_packets('DT10000Receiver5BDP.pcap', sender_ip, receiver_ip)

    # Merge on sequence number and IP ID to uniquely identify each packet transmission
    merged_packets = pd.merge(
        sender_packets,
        router_packets,
        on=['seq', 'ip_id'],
        how='left',
        indicator=True
    )

    # Identify packets that were sent by sender1 but not received at receiver
    # dropped_packets = merged_packets[merged_packets['_merge'] == 'left_only']
    merged_packets['dropped'] = merged_packets['_merge'] == 'left_only'
    P_uncond = merged_packets['dropped'].mean()
    merged_packets['prev_dropped'] = merged_packets['dropped'].shift(1)
    both_dropped = merged_packets['dropped'] & merged_packets['prev_dropped']
    N_prev_dropped = merged_packets['prev_dropped'].sum()
    N_both_dropped = both_dropped.sum()
    if N_prev_dropped > 0:
        P_cond = N_both_dropped / N_prev_dropped
    else:
        P_cond = 0

    print(f"Unconditional probability: {P_uncond:.4f}")
    print(f"Conditional probability: {P_cond:.4f}")
    # Reset index for clean output
    # dropped_packets = dropped_packets.reset_index(drop=True)

    # print("Packets dropped by router1:")
    # print(dropped_packets[['seq', 'ip_id', 'timestamp_x']])

    # Optionally, save to CSV
    # dropped_packets.to_csv('drop
    # ped_packets.csv', index=False)

if __name__ == '__main__':
    main()
