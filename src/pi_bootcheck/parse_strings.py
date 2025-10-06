import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import tldextract

# REGEXXXXAAAAHHHHHHHHHHHH
IP_RE = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
URL_RE = re.compile(r'\bhttps?://[^\s\'"<>]+', re.I)
DOMAIN_CANDIDATE_RE = re.compile(r'\b[a-z0-9][a-z0-9\.-]+\.[a-z]{2,}\b', re.I)
CERT_LIKE_RE = re.compile(r'-----BEGIN CERTIFICATE-----(?:.|\n)+?-----END CERTIFICATE-----', re.I | re.M)

def extract_indicators(text: str, min_len: int = 4) -> Dict[str, List[Tuple[str,int]]]:
    """
    Extract ips, urls, domains, cert-like blobs from a big text blob.
    Return dict with lists of (value, count)
    """
    ips = IP_RE.findall(text)
    urls = URL_RE.findall(text)
    certs = CERT_LIKE_RE.findall(text)
    # naive domains
    domains_found = DOMAIN_CANDIDATE_RE.findall(text)
    # canonicalize domains with tldextract
    domains_norm = []
    for d in domains_found:
        e = tldextract.extract(d)
        if e.domain:
            fullname = ".".join([part for part in (e.subdomain, e.domain, e.suffix) if part])
            if len(fullname) >= min_len:
                domains_norm.append(fullname.lower())
    # Score by frequency
    counters = {
        "ips": Counter(ips),
        "urls": Counter(urls),
        "domains": Counter(domains_norm),
        "certs": Counter(certs),
    }
    # Return top items as list of (value, count)
    result = {}
    for k, c in counters.items():
        result[k] = [(val, cnt) for val, cnt in c.most_common()]
    return result

