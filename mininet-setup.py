from mininet.net import Mininet
from mininet.node import Node, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

def redNetwork():
    "Create network with shared RED router."
    
    net = Mininet(link=TCLink, switch=OVSSwitch)

    # Topology
    # sender1 -----
    #               \
    #                router ----- receiver
    #               /
    # sender2 -----

    sender1 = net.addHost('sender1')
    sender2 = net.addHost('sender2')
    receiver = net.addHost('receiver')

    router = net.addHost('router')

    net.addLink(sender1, router, bw=3, delay='25ms')
    net.addLink(sender2, router, bw=3, delay='25ms')
    net.addLink(router, receiver, bw=1, delay='25ms')

    net.start()

    sender1.setIP('10.0.1.1/24', intf='sender1-eth0')
    sender2.setIP('10.0.2.1/24', intf='sender2-eth0')
    receiver.setIP('10.0.3.1/24', intf='receiver-eth0')
    router.setIP('10.0.1.254/24', intf='router-eth0')
    router.setIP('10.0.2.254/24', intf='router-eth1')
    router.setIP('10.0.3.254/24', intf='router-eth2')
    sender1.cmd('ip route add default via 10.0.1.254')
    sender2.cmd('ip route add default via 10.0.2.254')
    receiver.cmd('ip route add default via 10.0.3.254')

    router.cmd('sysctl -w net.ipv4.ip_forward=1')

    # RED
    router.cmd('tc qdisc add dev router-eth2 root handle 1: red limit 68 min 5 max 35 bandwidth 1mbit')

    # disable tso to avoid truckation of packet
    sender1.cmd('ethtool -K sender1-eth0 tso off')
    router.cmd('ethtool -K router-eth0 tso off')
    router.cmd('ethtool -K router-eth1 tso off')
    router.cmd('ethtool -K router-eth2 tso off')
    receiver.cmd('ethtool -K receiver-eth0 tso off')

    # set MTU, as our packet is around the size of 1000
    sender1.cmd('ifconfig sender1-eth0 mtu 1500')
    router.cmd('ifconfig router-eth0 mtu 1500')
    router.cmd('ifconfig router-eth1 mtu 1500')
    router.cmd('ifconfig router-eth2 mtu 1500')
    receiver.cmd('ifconfig receiver-eth0 mtu 1500')

    net.pingAll()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    redNetwork()
