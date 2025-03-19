
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/winsock2.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <netinet/in.h>
#include <arpa/inet.h>

typedef struct {
    char interface_name[32];
    int connection_status;
    char ip_address[16];
    int signal_strength;
} WiFiStatus;

static WiFiStatus current_wifi_status;

int get_wifi_connection_status(const char* interface) {
    struct ifreq ifr;
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    
    if (sock < 0) {
        return 0;
    }

    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, interface, IFNAMSIZ-1);

    if (ioctl(sock, SIOCGIFFLAGS, &ifr) < 0) {
        close(sock);
        return 0;
    }

    close(sock);
    return (ifr.ifr_flags & IFF_UP) && (ifr.ifr_flags & IFF_RUNNING);
}

char* get_wifi_ip_address(const char* interface) {
    struct ifreq ifr;
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    static char ip[16];
    
    if (sock < 0) {
        return NULL;
    }

    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, interface, IFNAMSIZ-1);
    
    if (ioctl(sock, SIOCGIFADDR, &ifr) < 0) {
        close(sock);
        return NULL;
    }

    close(sock);
    strcpy(ip, inet_ntoa(((struct sockaddr_in*)&ifr.ifr_addr)->sin_addr));
    return ip;
}

int get_signal_strength(const char* interface) {
    FILE* fp;
    char cmd[128];
    char buffer[256];
    int strength = 0;

    snprintf(cmd, sizeof(cmd), "iwconfig %s | grep 'Signal level' | awk '{print $4}' | cut -d'=' -f2", interface);
    fp = popen(cmd, "r");
    
    if (fp == NULL) {
        return 0;
    }

    if (fgets(buffer, sizeof(buffer), fp) != NULL) {
        strength = atoi(buffer);
    }
    
    pclose(fp);
    return strength;
}

void update_wifi_status(const char* interface) {
    strncpy(current_wifi_status.interface_name, interface, sizeof(current_wifi_status.interface_name) - 1);
    current_wifi_status.connection_status = get_wifi_connection_status(interface);
    
    if (current_wifi_status.connection_status) {
        char* ip = get_wifi_ip_address(interface);
        if (ip) {
            strncpy(current_wifi_status.ip_address, ip, sizeof(current_wifi_status.ip_address) - 1);
        }
        current_wifi_status.signal_strength = get_signal_strength(interface);
    } else {
        memset(current_wifi_status.ip_address, 0, sizeof(current_wifi_status.ip_address));
        current_wifi_status.signal_strength = 0;
    }
}

int toggle_wifi_connection(const char* interface, int enable) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "ip link set %s %s", interface, enable ? "up" : "down");
    return system(cmd) == 0;
}

WiFiStatus* get_current_wifi_status(void) {
    return ¤t_wifi_status;
}
