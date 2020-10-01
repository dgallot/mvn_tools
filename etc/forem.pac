function FindProxyForURL(url, host) {
 
// If the hostname matches, send direct.
    if (dnsDomainIs(host, "forem.be") ||
        shExpMatch(host, "(*.forem.be|neos.corp)"))
        return "DIRECT";
 
// If the requested website is hosted within the internal network, send direct.
    if (isPlainHostName(host) ||
        shExpMatch(host, "*.local") ||
        isInNet(dnsResolve(host), "10.0.0.0", "255.0.0.0") ||
        isInNet(dnsResolve(host), "172.16.0.0",  "255.240.0.0") ||
        isInNet(dnsResolve(host), "192.168.0.0",  "255.255.0.0") ||
        isInNet(dnsResolve(host), "127.0.0.0", "255.255.255.0"))
        return "DIRECT";
 
// DEFAULT RULE: All other traffic, use below proxies, in fail-over order.
   // return "PROXY 192.168.253.12:8080";
   return "PROXY proxy-guest.forem.be:8080";

}
