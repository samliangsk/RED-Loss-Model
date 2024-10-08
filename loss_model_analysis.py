import dpkt
import socket
import pandas as pd
import matplotlib.pyplot as plt
import sys

def detect_retransmissions(pcap_file, sender_ip, receiver_ip):

    sent_df, ack_df = parse_pcap(pcap_file, sender_ip, receiver_ip)

    retrans_df = identify_retransmissions(sent_df)

    if retrans_df.empty:
        print("No retransmissions detected.")
        return pd.DataFrame()

    mapped_retrans_df = map_retransmissions(sent_df, retrans_df)

    return mapped_retrans_df


def map_retransmissions(sent_df, retrans_df):

    merged_df = retrans_df.merge(
        sent_df.reset_index().rename(columns={'index': 'Original_Index'}),
        how='left',
        left_on='Original_Index',
        right_on='Original_Index',
        suffixes=('', '_original')
    )

    merged_df = merged_df.merge(
        sent_df.reset_index().rename(columns={'index': 'Retransmission_Index'}),
        how='left',
        left_on='Retransmission_Index',
        right_on='Retransmission_Index',
        suffixes=('', '_retransmission')
    )


    merged_df = merged_df[[
        'Retransmission_Index',
        'Retransmission_Time',
        'Original_Index',
        'Original_Time',
        'Seq',
        'Payload_Length'
    ]]

    return merged_df

def separate_original_retransmitted(sent_df, mapped_retrans_df):

    original_indices = mapped_retrans_df['Original_Index'].unique()
    original_packets = sent_df.iloc[original_indices].copy()
    original_packets['Retransmission_Count'] = sent_df.iloc[original_indices]['seq'].map(
        sent_df['seq'].value_counts()
    )

    retrans_indices = mapped_retrans_df['Retransmission_Index'].unique()
    retransmitted_packets = sent_df.iloc[retrans_indices].copy()

    return original_packets, retransmitted_packets


def identify_retransmissions1(sent_df):

    sent_df = sent_df.sort_values(by='timestamp').reset_index(drop=True)
    seq_dict = {}
    retransmissions = []

    for idx, row in sent_df.iterrows():
        seq = row['seq']
        timestamp = row['timestamp']
        payload_len = row['payload_len']

        if seq in seq_dict:
            # Retransmission
            original_idx = seq_dict[seq]['index']
            original_time = seq_dict[seq]['timestamp']

            retransmissions.append({
                'Retransmission_Index': idx,
                'Retransmission_Time': timestamp,
                'Original_Index': original_idx,
                'Original_Time': original_time,
                'Seq': seq,
                'Payload_Length': payload_len
            })
        else:
            # Normal
            seq_dict[seq] = {'index': idx, 'timestamp': timestamp}

    retrans_df = pd.DataFrame(retransmissions)

    return retrans_df


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

def identify_retransmissions(sent_df):

    sent_df = sent_df.sort_values('timestamp').reset_index(drop=True)

    sent_df['retransmission'] = sent_df.duplicated(subset=['seq'], keep='first')

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
    sent_df['status'] = 'Lost'

    # Normal: acknowledged and not a retrans
    sent_df.loc[(sent_df['acknowledged']) & (~sent_df['retransmission']), 'status'] = 'Normal'

    # Retransmission: acknowledged and is a retrans
    sent_df.loc[(sent_df['acknowledged']) & (sent_df['retransmission']), 'status'] = 'Retransmission'

    # Lost: default

    return sent_df


def main():
    pcap_file = 'RED10000p.pcap'
    sender_ip = '10.0.1.1'
    receiver_ip = '10.0.3.1'

    print("Parsing PCAP file...")
    sent_df, ack_df = parse_pcap(pcap_file, sender_ip, receiver_ip)
    # print(f"Total Sent Packets: {len(sent_df)}")
    # print(f"Total ACK Packets: {len(ack_df)}")

    # print("\nIdentifying retransmissions...")
    sent_df = identify_retransmissions(sent_df)
    num_retransmissions = sent_df['retransmission'].sum()
    print(f"Total Retransmissions: {num_retransmissions}")

    # print("\nDetermining acknowledged packets...")
    acknowledged = identify_acknowledged_packets(sent_df, ack_df)
    num_acknowledged = acknowledged.sum()
    print(f"Total Acknowledged Packets: {num_acknowledged}")

    print("\nClassifying packets...")
    classified_df = classify_packets(sent_df, acknowledged)
    num_normal = len(classified_df[classified_df['status'] == 'Normal'])
    num_retrans = len(classified_df[classified_df['status'] == 'Retransmission'])
    num_lost = len(classified_df[classified_df['status'] == 'Lost'])

    print("\nSummary Statistics:")
    print(f"Normal Packets: {num_normal}")
    print(f"Retransmissions: {num_retrans}")
    # print(f"Lost Packets: {num_lost}")
    # print(f"Packet Loss Rate: {num_lost / len(sent_df) * 100:.2f}%")
    print(f"Retransmission Rate: {num_retrans / len(sent_df) * 100:.2f}%")



    sent_df, ack_df = parse_pcap(pcap_file, sender_ip, receiver_ip)

    # Identify retransmissions
    temp = identify_retransmissions1(sent_df)

    if temp.empty:
        print("No retransmissions detected.")
        return pd.DataFrame()  # Return empty DataFrame

    # Map retransmissions to original packets
    mapped_retrans_df = map_retransmissions(sent_df, temp)
    # len(mapped_retrans_df.index)
    # len(sent_df.index)
    ori, retran = separate_original_retransmitted(sent_df,mapped_retrans_df)
    print("\nSummary Statistics:")
    print(f"Normal Packets: {len(sent_df.index) - len(retran.index)}")
    print(f"Retransmissions: {len(retran.index)}")
    # print(f"Lost Packets: {num_lost}")
    # print(f"Packet Loss Rate: {num_lost / len(sent_df) * 100:.2f}%")
    print(f"Retransmission Rate: {len(retran.index) / len(sent_df.index) * 100:.2f}%")

    print(f"original retran: {len(ori.index)}")


if __name__ == "__main__":
    main()
