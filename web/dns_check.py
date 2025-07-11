import dns.resolver

def check_dns_records(domain: str):
    results = {}
    # SPF
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        spf_records = [r.to_text().strip('"') for r in answers if r.to_text().startswith('"v=spf1')]
        if spf_records:
            results['spf'] = {'status': 'valid', 'value': spf_records[0]}
        else:
            results['spf'] = {'status': 'missing', 'value': ''}
    except Exception as e:
        results['spf'] = {'status': 'error', 'value': str(e)}
    # DKIM (mail selector)
    try:
        dkim_name = f"mail._domainkey.{domain}"
        answers = dns.resolver.resolve(dkim_name, 'TXT')
        dkim_records = [r.to_text().strip('"') for r in answers]
        if dkim_records:
            results['dkim'] = {'status': 'valid', 'value': dkim_records[0][:60] + '...'}
        else:
            results['dkim'] = {'status': 'missing', 'value': ''}
    except Exception as e:
        results['dkim'] = {'status': 'error', 'value': str(e)}
    # DMARC
    try:
        dmarc_name = f"_dmarc.{domain}"
        answers = dns.resolver.resolve(dmarc_name, 'TXT')
        dmarc_records = [r.to_text().strip('"') for r in answers if r.to_text().startswith('"v=DMARC1')]
        if dmarc_records:
            results['dmarc'] = {'status': 'valid', 'value': dmarc_records[0]}
        else:
            results['dmarc'] = {'status': 'missing', 'value': ''}
    except Exception as e:
        results['dmarc'] = {'status': 'error', 'value': str(e)}
    return results 