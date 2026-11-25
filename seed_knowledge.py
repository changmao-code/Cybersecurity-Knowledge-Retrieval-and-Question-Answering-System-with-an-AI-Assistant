"""Add sourced introductory notes, preserving existing records."""
from database import get_connection

# Original study summaries, not quotations from the linked publications.
ARTICLES = [
    ("ip-addressing", "networking", "IP addresses and IPv6", "Learn how addressing and routing help packets reach a destination.",
     "KEY IDEA\nIP addresses identify network interfaces. Routers use destination addresses and routing information to forward packets between networks.\n\nIPv6 uses 128-bit addresses, commonly written as hexadecimal groups separated by colons. IPv4 uses a different 32-bit address format.\n\nEXAMPLE\nThe IPv6 loopback address ::1 refers to the same computer. A loopback address cannot be used by another computer to reach your website.\n\nSECURITY CONNECTION\nAn IP address is not proof of a user's identity. Application authentication and access controls are still needed.\n\nCHECK YOUR UNDERSTANDING\nWhy would sharing a loopback address fail to let a friend open your website?",
     "RFC 8200 — Internet Protocol, Version 6", "https://www.rfc-editor.org/rfc/rfc8200.html"),
    ("udp-introduction", "networking", "What is UDP?", "Compare message-based UDP communication with TCP streams.",
     "KEY IDEA\nUDP sends individual datagrams between applications using source and destination ports. The protocol does not guarantee delivery, ordering or protection against duplicates.\n\nUnlike TCP, UDP does not establish a reliable byte stream. An application can add its own reliability mechanisms when required.\n\nEXAMPLE\nIf a receiver needs missing data to be sent again, the application must arrange that behaviour rather than assume UDP does it automatically.\n\nSECURITY CONNECTION\nUDP does not itself encrypt messages or authenticate the sender. A checksum is not a substitute for cryptographic protection.\n\nCHECK YOUR UNDERSTANDING\nWhich guarantees would an application have to add if it required messages to arrive in order?",
     "RFC 768 — User Datagram Protocol", "https://www.rfc-editor.org/rfc/rfc768.html"),
    ("dhcp-introduction", "networking", "What is DHCP?", "Understand automatic IPv4 configuration and address leases.",
     "KEY IDEA\nDHCP lets a client obtain an address and network configuration from a server. An address can be leased for a limited period and later renewed.\n\nA common initial exchange is DHCPDISCOVER, DHCPOFFER, DHCPREQUEST and DHCPACK. The client discovers servers, receives an offer, requests a configuration and receives acknowledgement.\n\nEXAMPLE\nAfter joining a network, a computer can receive configuration automatically rather than requiring someone to enter an address manually.\n\nSECURITY CONNECTION\nAccepting configuration affects where traffic goes. An unexpected DHCP server can therefore cause connectivity or security problems; network administrators must control who provides configuration.\n\nCHECK YOUR UNDERSTANDING\nHow does automatic address allocation differ from DNS name resolution?",
     "RFC 2131 — Dynamic Host Configuration Protocol", "https://www.rfc-editor.org/rfc/rfc2131.html"),
    ("http-introduction", "networking", "HTTP requests and responses", "Follow methods, status codes and the browser-to-backend request cycle.",
     "KEY IDEA\nHTTP defines requests and responses between clients and servers. A request includes a method and target; a response includes a status code and may contain a representation.\n\nGET requests retrieve a representation. POST asks the target resource to process the submitted content according to its own rules. A 200 response indicates success; 404 means the requested resource was not found.\n\nEXAMPLE\nYour browser requests /api/topics/networking. The Python backend queries MySQL and returns JSON, which the page renders as resource cards.\n\nSECURITY CONNECTION\nHTTP application semantics do not by themselves encrypt traffic. HTTPS adds protection using TLS. Avoid placing passwords in URL query strings.\n\nCHECK YOUR UNDERSTANDING\nWhy can the page load while a separate API request returns 404?",
     "RFC 9110 — HTTP Semantics", "https://www.rfc-editor.org/rfc/rfc9110.html"),
    ("tls-introduction", "networking", "HTTPS and TLS", "Understand encrypted transport, integrity and server authentication.",
     "KEY IDEA\nTLS protects communication between applications against eavesdropping and tampering. HTTPS uses TLS to protect HTTP traffic.\n\nDuring a typical certificate-based connection, the client validates the server certificate and the peers establish keys for protecting application data. Encryption and authentication serve different purposes.\n\nEXAMPLE\nA login form sent over HTTPS is protected in transit. The server must still hash stored passwords and decide which records each user may access.\n\nSECURITY CONNECTION\nA valid HTTPS connection does not establish that a website's content is trustworthy. It also does not protect information after a compromised endpoint has decrypted it.\n\nCHECK YOUR UNDERSTANDING\nWhy are password hashing and access controls still necessary when a site uses HTTPS?",
     "RFC 8446 — Transport Layer Security 1.3", "https://www.rfc-editor.org/rfc/rfc8446.html"),
    ("firewall-introduction", "networking", "Firewalls and network boundaries", "Understand how firewall policies control permitted network traffic.",
     "KEY IDEA\nA firewall controls traffic between hosts or networks according to a policy. Rules can allow or deny traffic based on properties such as addresses, protocols and ports.\n\nHost-based firewalls protect an individual computer. Network firewalls help control traffic crossing network boundaries. Their effectiveness depends on suitable rules and ongoing management.\n\nEXAMPLE\nA web backend can connect to a database on the same computer without making the database directly accessible to other computers.\n\nSECURITY CONNECTION\nAllow only the connections required for a service. A firewall cannot replace secure application code, account permissions or updates. Test both expected access and expected blocking when changing rules.\n\nCHECK YOUR UNDERSTANDING\nWhy does publishing a website not automatically require publishing its database port?",
     "NIST SP 800-41 Rev. 1 — Guidelines on Firewalls and Firewall Policy", "https://csrc.nist.gov/pubs/sp/800/41/r1/final"),
    ("authentication-basics", "cryptography", "Authentication and account protection", "Learn how passwords, sessions and additional factors protect accounts.",
     "KEY IDEA\nAuthentication verifies a claimed identity. Authorization determines what that identity may do. A successful login does not give a user permission to access every record.\n\nStore passwords using a suitable password hashing function rather than plaintext. Protect login traffic with TLS and use additional authentication factors where appropriate.\n\nEXAMPLE\nA student can log in to view their own results while an administrator has separate permissions for managing learning resources.\n\nCHECK YOUR UNDERSTANDING\nWhy should a database password and a student's website password serve separate roles?",
     "OWASP — Authentication Cheat Sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html"),
    ("sql-injection-basics", "web-security", "Preventing SQL injection", "Keep SQL statements separate from user-supplied search and login values.",
     "KEY IDEA\nSQL injection occurs when untrusted input changes the structure of a database command. Constructing SQL by joining user input into the statement can create this risk.\n\nUse parameterized queries: write the SQL structure separately and pass input values through the database driver's parameter interface.\n\nEXAMPLE\nA search term containing an apostrophe should be treated as search text, not as part of a SQL command.\n\nSECURITY CONNECTION\nGive the application database account only the permissions it needs. Input validation is useful, but it does not replace parameterized queries.\n\nCHECK YOUR UNDERSTANDING\nWhat is the difference between a placeholder and concatenating search text into SQL?",
     "OWASP — SQL Injection Prevention Cheat Sheet", "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"),
    ("privacy-basics", "privacy", "Protecting personal information", "Think about the information a website collects, exposes and retains.",
     "KEY IDEA\nPrivacy protection includes reducing unnecessary exposure of personal information. Consider what users disclose, how communication is protected and how account information may reveal their identity.\n\nUse protected connections and avoid exposing sensitive information through public pages or careless error messages. Explain relevant privacy choices to users.\n\nEXAMPLE\nA public learning-resource page should not display a list of students' account details. A user should be able to browse educational material without seeing another person's private information.\n\nCHECK YOUR UNDERSTANDING\nWhich pieces of account information would be unnecessary to show on a public homepage?",
     "OWASP — User Privacy Protection Cheat Sheet", "https://cheatsheetseries.owasp.org/cheatsheets/User_Privacy_Protection_Cheat_Sheet.html"),
]


ARTICLES[:0] = [('dns-introduction', 'networking', 'What is DNS?', 'Understand how domain names relate to network resources.', 'The Domain Name System (DNS) is a distributed, hierarchical naming system. It stores resource records associated with domain names.\n\nA common use is looking up an IP address for a hostname. DNS also supports other information, such as mail-routing records.\n\nResolvers query DNS servers and can cache results for a limited time. DNS is more than a single central address book.', 'RFC 1034 — Domain Names: Concepts and Facilities', 'https://www.rfc-editor.org/rfc/rfc1034.html'), ('tcp-introduction', 'networking', 'What is TCP?', 'Explore reliable, ordered communication between applications.', 'The Transmission Control Protocol (TCP) provides a reliable, in-order byte-stream service between applications.\n\nIt uses sequence numbers and acknowledgements to track data. Lost data can be retransmitted. Flow control helps prevent a sender from overwhelming the receiver.\n\nTCP does not itself encrypt application data. Protocols such as TLS can provide protection above the transport layer.', 'RFC 9293 — Transmission Control Protocol', 'https://www.rfc-editor.org/rfc/rfc9293.html')]


def seed_knowledge():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            for article in ARTICLES:
                cursor.execute("SELECT id FROM knowledge_articles WHERE slug = %s", (article[0],))
                if cursor.fetchone() is not None:
                    continue
                cursor.execute("""
                    INSERT INTO knowledge_articles
                    (slug, topic, title, summary, content, source_title, source_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, article)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    seed_knowledge()
    print("[OK] Additional learning resources are stored in MySQL.")
