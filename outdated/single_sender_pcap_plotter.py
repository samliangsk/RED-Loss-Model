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

def plot_seq_ack(sent_times, sent_seqs, ack_times, ack_acks):
    plt.figure(figsize=(12, 6))

    # Plot SEQ
    plt.scatter(sent_times, sent_seqs, s=0.5, color='blue', label='Sent Seq')

    # Plot ACK
    plt.scatter(ack_times, ack_acks, s=0.5, color='red', label='ACKs')

    plt.xlabel('Time (s)')
    plt.ylabel('Sequence / Acknowledgment Number')
    plt.title('TCP Sequence Numbers and ACKs Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    pcap_file = 'sender8-REDlimit12500prob0_1.pcap'

    sender_ip = '10.0.1.1'
    receiver_ip = '10.0.3.1'

    sent_times, sent_seqs, ack_times, ack_acks = parse_pcap(pcap_file, sender_ip, receiver_ip)

    start_seq = sent_seqs[0] if sent_seqs else 0
    sent_seqs = [s - start_seq for s in sent_seqs]
    ack_acks = [s - start_seq for s in ack_acks]

    start_time = min(sent_times[0], ack_times[0]) if sent_times and ack_times else 0
    sent_times = [t - start_time for t in sent_times]
    ack_times = [t - start_time for t in ack_times]


    plot_seq_ack(sent_times, sent_seqs, ack_times, ack_acks)

if __name__ == '__main__':
    main()
