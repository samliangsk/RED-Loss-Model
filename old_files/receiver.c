#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define LISTEN_PORT 5001
#define BUFFER_SIZE 1024

int main() {
    int listen_fd, conn_fd;
    struct sockaddr_in servaddr, cliaddr;
    socklen_t cliaddr_len;
    char buffer[BUFFER_SIZE];

    if ((listen_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = INADDR_ANY;  // Listen on all interfaces
    servaddr.sin_port = htons(LISTEN_PORT);

    if (bind(listen_fd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("Bind failed");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }

    if (listen(listen_fd, 5) < 0) {
        perror("Listen failed");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }

    printf("Receiver is listening on port %d...\n", LISTEN_PORT);

    cliaddr_len = sizeof(cliaddr);
    if ((conn_fd = accept(listen_fd, (struct sockaddr *)&cliaddr, &cliaddr_len)) < 0) {
        perror("Accept failed");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }

    printf("Connection accepted from %s:%d\n",
           inet_ntoa(cliaddr.sin_addr), ntohs(cliaddr.sin_port));

    ssize_t bytes_received;
    while ((bytes_received = recv(conn_fd, buffer, BUFFER_SIZE, 0)) > 0) {
    }

    if (bytes_received < 0) {
        perror("Receive failed");
    }

    close(conn_fd);
    close(listen_fd);
    return 0;
}
