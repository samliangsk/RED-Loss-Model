all:
	gcc -o sender sender.c -lpcap -lpthread
	gcc -o receiver receiver.c -lpcap -lpthread

sender: 
	gcc -o sender sender.c -lpcap -lpthread

receiver:
	gcc -o receiver receiver.c -lpcap -lpthread

clean:
	rm -f sender receiver