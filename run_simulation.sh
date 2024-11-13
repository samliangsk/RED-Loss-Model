# collect BW from 1mbps to 10mbps
# collect RTT from 10ms to 400ms

for (( i=10; i<=100; i+=1 ))
do
    for((j=4; j<=400; j+=4))
    do
        # Calculate the bandwidth value
        bw=$(echo "scale=1; $i/10" | bc)
        delay=$(echo "scale=0; $j/4" | bc)

        # Replace '.' with 'p' for filenames
        bw_str=$(echo $bw | sed 's/\./p/')
        delay_str=$(echo $j)
        # Generate the base filename with the current bandwidth
        fname_base="CD-bw${bw_str}Mb-dlay${delay_str}-b450p"
        
        # Display the current simulation parameters
        echo "Running simulation with bandwidth ${bw}Mbps, RTT ${delay_str}ms, output files base ${fname_base}"
        
        # Run the ns-3 simulation with the specified parameters
        ./ns3 run "scratch/lost-topo.cc --bottleneckBandwidth=${bw}Mbps --accessDelay=${delay}ms --bottleneckDelay=${delay}ms --dropTrFileName=${fname_base}-drp.tr"
    done
done
