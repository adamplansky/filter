Port scans
- port scanning reported by honeypots (Node.SW = LaBrea, Dionaea) or netflow analysis systems (HostStatsNemea, FlowmonADS).
- portscan3 shows that Target may be partially anonymized (to not disclose address of the honeypot)

Login
- Dictionary/bruteforce login attempts detected by honeypots or netflow analysis systems

Expliot
- Attempt to exploit some common vulnerability reported by a honeypot

DDoS
- detected or suspected DDoS attacks (or parts of them)
- ddos1 reports a DNS server misused for amplification attack
- ddos2 and ddo3 reports abnormally high traffic to signle IP - probable DDoS attack

Vulnerable
- Report about a vulnerable/misuasable configuration as reported to us by ShadowServer
- In this case it reports a server in our network usable to amplification attacks

Botnet
- Reports about host that are probably part of a botnet, in both cases detected as a connection to known CC server
- botnet1 - report received from an external system
- botnet2 - connection detected by our monitoring system

Anomaly
- various traffic anomalies
- anomaly1 also contains a sample of netflow data
