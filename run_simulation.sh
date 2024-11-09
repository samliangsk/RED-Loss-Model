for (( i=10; i<=100; i+=1 ))
do
    # Calculate the bandwidth value
    bw=$(echo "scale=1; $i/10" | bc)
    
    # Replace '.' with 'p' for filenames
    bw_str=$(echo $bw | sed 's/\./p/')
    
    # Generate the base filename with the current bandwidth
    fname_base="CD-bw${bw_str}Mb-dlay100-b450p"
    
    # Display the current simulation parameters
    echo "Running simulation with bandwidth ${bw}Mbps, output files base ${fname_base}"
    
    # Run the ns-3 simulation with the specified parameters
    ./ns3 run "scratch/lost-topo.cc --bottleneckBandwidth=${bw}Mbps --dropTrFileName=${fname_base}-drp.tr"
done