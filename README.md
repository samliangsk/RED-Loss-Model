# Re-evaluate Internet Traffic Loss Models

This is an on-going research project for CSCI651 @ USC Viterbi, by Qishen Sam Liang.

Mentor: Prof. John Heidemann.

# Codes

## lost-topo.cc

The NS3 for the simulation to run. To run it, first install NS3 via the [official instruction]{https://www.nsnam.org/}.

Copy the file to scratch in the folder and call `./ns3 run scratch/loss-topo.cc`

## buf-pcap-plot.py

The Python parser and ploter that takes the input of *.pcap and *-buf.tr and file plot the data packet SEQ, coresponding ACK, and the router buffer queue length (in packet).

## loss-model-analysis.py

The Python parser that do conditional and unconditional loss probability calculations. Input: *.pcap and *-drp.tr.

# Data

Data naming follows the following form

[Type]-bw[bw]-b[buf]-[data].[datatype]

## Type

The congestion control algorithm at the router

DT - Drop-tail
RED - Random Early Detection
CD - CoDel

## bw

The bottleneck bandwidth

example: 1Mb

## buf

The maximum or total buffer size (in packets)

example: 9p

## Data

-cwn congestion window

-buf buffer length (in packets)

-drp packet dropped by router (SEQ)

## Datatype

.tr traces

.pcap packet capture
