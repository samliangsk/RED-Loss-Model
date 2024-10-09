import dpkt
import socket
import pandas as pd
# import matplotlib.pyplot as plt
import sys


def ip_to_str(address):
    return socket.inet_ntoa(address)

def parse_pcap(pcap_file, sender_ip, receiver_ip):

    sent_packets = []
    ack_packets = []

    with open(pcap_file, 'rb') as f:
        try:
            pcap = dpkt.pcap.Reader(f)
        except (dpkt.dpkt.NeedData, dpkt.dpkt.UnpackError):
            print("Error: Unable to read PCAP file.")
            sys.exit(1)

        for timestamp, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                if not isinstance(eth.data, dpkt.ip.IP):
                    continue
                ip = eth.data

                if isinstance(ip, dpkt.ip.IP):
                    src_ip = ip_to_str(ip.src)
                    dst_ip = ip_to_str(ip.dst)
                else:
                    continue 

                if not isinstance(ip.data, dpkt.tcp.TCP):
                    continue
                tcp = ip.data

                if src_ip == sender_ip and dst_ip == receiver_ip:
                    sent_packets.append({
                        'timestamp': timestamp,
                        'seq': tcp.seq,
                        'payload_len': len(tcp.data)
                    })


                elif src_ip == receiver_ip and dst_ip == sender_ip:
                    if tcp.flags & dpkt.tcp.TH_ACK:
                        ack_packets.append({
                            'timestamp': timestamp,
                            'ack': tcp.ack
                        })

            except Exception:
                continue

    sent_df = pd.DataFrame(sent_packets)
    ack_df = pd.DataFrame(ack_packets)

    return sent_df, ack_df

def identify_Loss(sent_df):

    sent_df = sent_df.sort_values('timestamp').reset_index(drop=True)

    sent_df['Loss'] = sent_df.duplicated(subset=['seq'], keep='last')

    return sent_df

def identify_acknowledged_packets(sent_df, ack_df):

    if ack_df.empty:
        return pd.Series([False] * len(sent_df), index=sent_df.index)


    ack_df = ack_df.sort_values('timestamp').reset_index(drop=True)
    ack_df['max_ack'] = ack_df['ack'].cummax()

    sent_seq_end = sent_df['seq'] + sent_df['payload_len']
    ack_matrix = ack_df['max_ack'].values[:, None] >= sent_seq_end.values

    acknowledged = ack_matrix.any(axis=0)

    return acknowledged

def classify_packets(sent_df, acknowledged):

    sent_df = sent_df.copy()
    sent_df['acknowledged'] = acknowledged

    # Initialize to Lost
    sent_df['status'] = 'Unknown'

    # Normal: acknowledged and not a retrans
    sent_df.loc[(sent_df['acknowledged']) & (~sent_df['Loss']), 'status'] = 'Normal'

    # Retransmission: acknowledged and is a retrans
    sent_df.loc[(sent_df['acknowledged']) & (sent_df['Loss']), 'status'] = 'Lost'

    return sent_df


def main():
    pcap_file = 'RED10000p_!S_!fsretran.pcap'
    sender_ip = '10.0.1.1'
    receiver_ip = '10.0.3.1'


    print(f"From {pcap_file}")
    sent_df, ack_df = parse_pcap(pcap_file, sender_ip, receiver_ip)

    sent_df = identify_Loss(sent_df)
    num_lost = sent_df['Loss'].sum()

    acknowledged = identify_acknowledged_packets(sent_df, ack_df)
    num_acknowledged = acknowledged.sum()
    print(f"Total Acknowledged Packets: {num_acknowledged}")

    classified_df = classify_packets(sent_df, acknowledged)
    num_normal = len(classified_df[classified_df['status'] == 'Normal'])
    num_lost = len(classified_df[classified_df['status'] == 'Lost'])
    num_unknown = len(classified_df[classified_df['status'] == 'Unknown'])

    print("\nSummary Statistics:")
    print(f"Normal Packets: {num_normal}")
    print(f"Lost: {num_lost}")
    print(f"Loss Rate: {num_lost / len(sent_df) * 100:.2f}%")

    previous_loss = sent_df['Loss'].shift(1)

    both_true = (sent_df['Loss'] == True) & (previous_loss == True)
    both_true_count = both_true.sum()
    previous_true_count = (previous_loss == True).sum()

    # Conditional probability : P(current_lost|previous_lost) = P(cur_lost && prev_lost) / P(prev_lost)
    conditional_probability = both_true_count / previous_true_count if previous_true_count != 0 else 0

    print(f"Conditional probability: {conditional_probability *100:.2f}%")

if __name__ == "__main__":
    main()
