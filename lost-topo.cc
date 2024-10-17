/*
 * Copyright (c) 2014 ResiliNets, ITTC, University of Kansas
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * Author: Truc Anh N Nguyen <trucanh524@gmail.com>
 * Modified by:   Pasquale Imputato <p.imputato@gmail.com>
 * Modified by:   Qishen Sam Liang <samliangsk@gmail.com>
 * 
 */

/*
 * This is a basic example that compares CoDel and PfifoFast and RED queues using a simple, single-flow
 * topology:
 *
 * source -------------------------- router ------------------------ sink
 *          100 Mb/s, 0.1 ms       pfifofast       5 Mb/s, 5ms
 *                                 or codel        bottleneck
 *
 * The source generates traffic across the network using BulkSendApplication.
 * The default TCP version in ns-3, TcpNewReno, is used as the transport-layer protocol.
 * Packets transmitted during a simulation run are captured into a .pcap file, and
 * congestion window values are also traced.
 */


// add queue item track
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/enum.h"
#include "ns3/error-model.h"
#include "ns3/event-id.h"
#include "ns3/internet-module.h"
#include "ns3/ipv4-global-routing-helper.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/tcp-header.h"
#include "ns3/traffic-control-module.h"
#include "ns3/udp-header.h"
#include "ns3/config-store-module.h" 
#include <fstream>
#include <iostream>
#include <string>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("CoDel-Droptail-RED-BasicTest");

/**
 * Function called when Congestion Window is changed.
 *
 * \param stream Output stream.
 * \param oldval Old value.
 * \param newval New value.
 */
static void
CwndTracer(Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval)
{
    *stream->GetStream() << oldval << " " << newval << std::endl;
}

/**
 * Function to enable the Congestion window tracing.
 *
 * Note that you can not hook to the trace before the socket is created.
 *
 * \param cwndTrFileName Name of the output file.
 */


/**
 * Function called when Congestion Window is changed.
 *
 * \param stream Output stream.
 * \param oldval Old value.
 * \param newval New value.
 */


static void
TraceCwnd(std::string cwndTrFileName)
{
    AsciiTraceHelper ascii;
    if (cwndTrFileName.empty())
    {
        NS_LOG_DEBUG("No trace file for cwnd provided");
        return;
    }
    else
    {
        Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream(cwndTrFileName);
        Config::ConnectWithoutContext(
            "/NodeList/1/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow",
            MakeBoundCallback(&CwndTracer, stream));
    }
}

static void
BufTracerfifo(Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval)
{
    *stream->GetStream() << newval << std::endl;
}

/**
 * Function to enable the Congestion window tracing.
 *
 * Note that you can not hook to the trace before the socket is created.
 *
 * \param bufTrFileName Name of the output file.
 */


static void
TraceBuffifo(std::string bufTrFileName)
{
    AsciiTraceHelper ascii;
    if (bufTrFileName.empty())
    {
        NS_LOG_DEBUG("No trace file for buf provided");
        return;
    }
    else
    {
        Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream(bufTrFileName);
        Config::ConnectWithoutContext(
            "/NodeList/0/$ns3::Node/$ns3::TrafficControlLayer/RootQueueDiscList/2/PacketsInQueue",
            MakeBoundCallback(&BufTracerfifo, stream));
    }
}


int
main(int argc, char* argv[])
{
    std::string bottleneckBandwidth = "2Mbps";
    std::string bottleneckDelay = "25ms";
    std::string accessBandwidth = "6Mbps";
    std::string accessDelay = "25ms";
    
    std::string queueDiscType = "CoDel"; // PfifoFast(Droptail) or CoDel or RED
    uint32_t queueDiscSize = 125;            // in packets
    uint32_t queueSize = 10;                 // in packets
    uint32_t pktSize = 1458;                 // in bytes. 1458 to prevent fragments
    float startTime = 0.1F;
    float simDuration = 60;                  // in seconds

    bool isPcapEnabled = true;
    std::string pcapFileName = "CD-bw2Mb-b125p";
    std::string cwndTrFileName = "CD-bw2Mb-b125p-cwn.tr";
    std::string bufTrFileName = "CD-bw2Mb-b125p-buf.tr";
    bool logging = false;

    CommandLine cmd(__FILE__);
    cmd.AddValue("bottleneckBandwidth", "Bottleneck bandwidth", bottleneckBandwidth);
    cmd.AddValue("bottleneckDelay", "Bottleneck delay", bottleneckDelay);
    cmd.AddValue("accessBandwidth", "Access link bandwidth", accessBandwidth);
    cmd.AddValue("accessDelay", "Access link delay", accessDelay);
    cmd.AddValue("queueDiscType", "Bottleneck queue disc type: PfifoFast, CoDel", queueDiscType);
    cmd.AddValue("queueDiscSize", "Bottleneck queue disc size in packets", queueDiscSize);
    cmd.AddValue("queueSize", "Devices queue size in packets", queueSize);
    cmd.AddValue("pktSize", "Packet size in bytes", pktSize);
    cmd.AddValue("startTime", "Simulation start time", startTime);
    cmd.AddValue("simDuration", "Simulation duration in seconds", simDuration);
    cmd.AddValue("isPcapEnabled", "Flag to enable/disable pcap", isPcapEnabled);
    cmd.AddValue("pcapFileName", "Name of pcap file", pcapFileName);
    cmd.AddValue("cwndTrFileName", "Name of cwnd trace file", cwndTrFileName);
    cmd.AddValue("logging", "Flag to enable/disable logging", logging);
    cmd.Parse(argc, argv);

    float stopTime = startTime + simDuration;

    if (logging)
    {
        LogComponentEnable("CoDelPfifoFastBasicTest", LOG_LEVEL_ALL);
        LogComponentEnable("BulkSendApplication", LOG_LEVEL_INFO);
        LogComponentEnable("PfifoFastQueueDisc", LOG_LEVEL_ALL);
        LogComponentEnable("CoDelQueueDisc", LOG_LEVEL_ALL);
    }

    // Enable checksum
    if (isPcapEnabled)
    {
        GlobalValue::Bind("ChecksumEnabled", BooleanValue(true));
    }

    // Devices queue configuration
    Config::SetDefault("ns3::DropTailQueue<Packet>::MaxSize",
                       QueueSizeValue(QueueSize(QueueSizeUnit::PACKETS, queueSize)));

    // Create gateway, source, and sink
    NodeContainer gateway;
    gateway.Create(1);
    NodeContainer source;
    source.Create(1);
    NodeContainer sink;
    sink.Create(1);

    // Create and configure access link and bottleneck link
    PointToPointHelper accessLink;
    accessLink.SetDeviceAttribute("DataRate", StringValue(accessBandwidth));
    accessLink.SetChannelAttribute("Delay", StringValue(accessDelay));

    PointToPointHelper bottleneckLink;
    bottleneckLink.SetDeviceAttribute("DataRate", StringValue(bottleneckBandwidth));
    bottleneckLink.SetChannelAttribute("Delay", StringValue(bottleneckDelay));

    InternetStackHelper stack;
    stack.InstallAll();

    // Access link traffic control configuration
    TrafficControlHelper tchPfifoFastAccess;
    tchPfifoFastAccess.SetRootQueueDisc("ns3::PfifoFastQueueDisc", "MaxSize", StringValue("1000p"));

    // Bottleneck link traffic control configuration
    TrafficControlHelper tchPfifo;
    tchPfifo.SetRootQueueDisc("ns3::PfifoFastQueueDisc",
                              "MaxSize",
                              StringValue(std::to_string(queueDiscSize) + "p"));

    TrafficControlHelper tchCoDel;
    tchCoDel.SetRootQueueDisc("ns3::CoDelQueueDisc");
    Config::SetDefault("ns3::CoDelQueueDisc::MaxSize",
                       StringValue(std::to_string(queueDiscSize) + "p"));

    Ipv4AddressHelper address;
    address.SetBase("10.0.0.0", "255.255.255.0");

    // Configure the source and sink net devices
    // and the channels between the source/sink and the gateway
    Ipv4InterfaceContainer sinkInterface;

    NetDeviceContainer devicesAccessLink;
    NetDeviceContainer devicesBottleneckLink;

    devicesAccessLink = accessLink.Install(source.Get(0), gateway.Get(0));
    tchPfifoFastAccess.Install(devicesAccessLink);
    address.NewNetwork();
    Ipv4InterfaceContainer interfaces = address.Assign(devicesAccessLink);

    devicesBottleneckLink = bottleneckLink.Install(gateway.Get(0), sink.Get(0));
    address.NewNetwork();
    QueueDiscContainer qdiscs;
    if (queueDiscType == "PfifoFast")
    {
        tchPfifo.Install(devicesBottleneckLink);
    }
    else if (queueDiscType == "CoDel")
    {
        tchCoDel.Install(devicesBottleneckLink);
    }
    else
    {
        NS_ABORT_MSG(
            "Invalid queue disc type: Use --queueDiscType=PfifoFast or --queueDiscType=CoDel");
    }
    interfaces = address.Assign(devicesBottleneckLink);

    sinkInterface.Add(interfaces.Get(1));

    // inserting qdisc callbacks

    // Ptr<QueueDisc> qdisc = qdiscs.Get(0)
    // qdisc->TraceConnectWithoutContext("PacketsInQueue",MakeCallback(&bufTracer))


    NS_LOG_INFO("Initialize Global Routing.");
    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    uint16_t port = 50000;
    Address sinkLocalAddress(InetSocketAddress(Ipv4Address::GetAny(), port));
    PacketSinkHelper sinkHelper("ns3::TcpSocketFactory", sinkLocalAddress);

    // Configure application
    AddressValue remoteAddress(InetSocketAddress(sinkInterface.GetAddress(0, 0), port));
    Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(pktSize));
    BulkSendHelper ftp("ns3::TcpSocketFactory", Address());
    ftp.SetAttribute("Remote", remoteAddress);
    ftp.SetAttribute("SendSize", UintegerValue(pktSize));
    ftp.SetAttribute("MaxBytes", UintegerValue(0));

    ApplicationContainer sourceApp = ftp.Install(source.Get(0));
    sourceApp.Start(Seconds(0));
    sourceApp.Stop(Seconds(stopTime - 3));

    sinkHelper.SetAttribute("Protocol", TypeIdValue(TcpSocketFactory::GetTypeId()));
    ApplicationContainer sinkApp = sinkHelper.Install(sink);
    sinkApp.Start(Seconds(0));
    sinkApp.Stop(Seconds(stopTime));

    Simulator::Schedule(Seconds(0.00001), &TraceCwnd, cwndTrFileName);
    
    Simulator::Schedule(Seconds(0.00001), &TraceBuffifo, bufTrFileName);
    

    if (isPcapEnabled)
    {
        accessLink.EnablePcap(pcapFileName, source, true);
    }

    Simulator::Stop(Seconds(stopTime));

    // // Output config store to txt format
    // Config::SetDefault ("ns3::ConfigStore::Filename", StringValue
    // ("output-attributes.txt"));
    // Config::SetDefault ("ns3::ConfigStore::FileFormat", StringValue
    // ("RawText"));
    // Config::SetDefault ("ns3::ConfigStore::Mode", StringValue ("Save"));
    // ConfigStore outputConfig2;
    // outputConfig2.ConfigureAttributes (); 
    Simulator::Run();

    Simulator::Destroy();
    return 0;
}
