ami-0b0ea68c435eb488d


Flask==0.12.2 
Werkzeug==0.14.1 
Jinja2==2.10 
itsdangerous==0.24 
click==6.7 
MarkupSafe==1.0


## Vulnerability Summary for Your Scanner

| Area | Legacy Pattern | Vulnerability |
|---|---|---|
| Python version | Python 2.7 (EOL Jan 2020) | No security patches |
| Flask version | 0.12.2 | CVE-2018-1000656 (DoS) |
| Werkzeug | 0.14.1 | CVE-2019-14806 (pin brute-force) |
| Password hashing | MD5 (no salt) | Easily crackable |
| SQL queries | String concatenation | SQL Injection |
| Secret key | Hardcoded string | Credential exposure |
| Debug mode | `debug=True` in prod | Remote code execution risk |
| OS | Ubuntu 16.04 (EOL Apr 2021) | Unpatched kernel/libs |
| Bootstrap | 3.3.7 | XSS in tooltip/popover |
| jQuery | 1.12.4 | CVE-2019-11358 (prototype pollution) |
| Running as root | `sudo python` on port 80 | Full system compromise if exploited |
| No CSRF protection | No tokens on forms | CSRF attacks |
| No session expiry | Permanent sessions | Session hijacking |