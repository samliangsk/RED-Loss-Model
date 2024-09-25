#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>         // For close()
#include <sys/socket.h>     // For socket functions
#include <arpa/inet.h>      // For inet_pton()
#include <netinet/tcp.h>    // For TCP_NODELAY
#include <netinet/in.h>     // For sockaddr_in
#include <errno.h>          // For errno

#define SERVER_IP "10.0.3.1"   // Receiver's IP address
#define SERVER_PORT 5001       // Receiver's port
#define PACKET_SIZE 1000       // Size of each packet in bytes
#define NUM_PACKETS 500        // Total number of packets to send

int main() {
    int sockfd;
    struct sockaddr_in servaddr;
    char *buffer = malloc(PACKET_SIZE);
    if (!buffer) {
        perror("Failed to allocate buffer");
        exit(EXIT_FAILURE);
    }
    memset(buffer, 'A', PACKET_SIZE);  // Fill the buffer with 'A's

    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("Socket creation failed");
        free(buffer);
        exit(EXIT_FAILURE);
    }

    int flag = 1;
    if (setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY, (char *)&flag, sizeof(int)) != 0) {
        perror("setsockopt TCP_NODELAY failed");
        close(sockfd);
        free(buffer);
        exit(EXIT_FAILURE);
    }

    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(SERVER_PORT);

    if (inet_pton(AF_INET, SERVER_IP, &servaddr.sin_addr) <= 0) {
        perror("Invalid address/Address not supported");
        close(sockfd);
        free(buffer);
        exit(EXIT_FAILURE);
    }

    if (connect(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("Connection failed");
        close(sockfd);
        free(buffer);
        exit(EXIT_FAILURE);
    }

    ssize_t bytes_sent;
    for (int i = 0; i < NUM_PACKETS; i++) {
        bytes_sent = send(sockfd, buffer, PACKET_SIZE, 0);
        if (bytes_sent < 0) {
            perror("Send failed");
            break;
        }
        printf("p# %d\n",i);
    }

    close(sockfd);
    free(buffer);
    return 0;
}
