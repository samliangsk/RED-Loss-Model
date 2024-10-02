from pyroute2 import IPRoute
import time

def main():
    ip = IPRoute()
    interface = 'router-eth2'


    try:
        idx = ip.link_lookup(ifname=interface)[0]
    except IndexError:
        print(f"Interface {interface} not found.")
        return

    with open('./queue.log', 'w') as logfile:
        logfile.write('timestamp,backlog_bytes,drops,queue_length\n')
        try:
            while True:
                stats = ip.get_qdiscs(index=idx)
                for qdisc in stats:
                    if 'attrs' in qdisc:
                        attrs = dict(qdisc['attrs'])
                        qdisc_stats = qdisc.get('stats2', {}).get('qstats', {})
                        qdisc_kind = attrs.get('TCA_KIND', '')
                        backlog_bytes = qdisc_stats.get('backlog', 0)
                        drops = qdisc_stats.get('drops', 0)
                        packets = qdisc_stats.get('packets', 0)
                        timestamp = time.time()
                        logfile.write(f"{timestamp},{backlog_bytes},{drops},{packets}\n")
                logfile.flush()
                time.sleep(0.001)
        except KeyboardInterrupt:
            print("Monitoring stopped.")

if __name__ == '__main__':
    main()
