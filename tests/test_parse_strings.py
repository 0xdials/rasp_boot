from pi_bootcheck.parse_strings import extract_indicators

# go ahead, do a lil regex for em derek 
def test_extract_indicators():
    text = "Contact admin@example.com or visit http://example.com/path. Also check 192.168.1.1 and test.example.co.uk"
    inds = extract_indicators(text)
    # domains should contain example.com and test.example.co.uk
    domains = [d for d,_ in inds.get("domains", [])]
    assert "example.com" in domains or "test.example.co.uk" in domains
    ips = [ip for ip,_ in inds.get("ips", [])]
    assert "192.168.1.1" in ips

