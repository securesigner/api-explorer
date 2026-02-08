# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it through [GitHub Security Advisories](https://github.com/securesigner/api-explorer/security/advisories/new).

**Do not open a public issue for security vulnerabilities.**

GitHub Security Advisories allow us to discuss and fix the issue privately before any public disclosure.

## Scope

This project is a client-side web application with no backend server, authentication, or user data storage. Security concerns most likely involve:

- XSS vulnerabilities in rendered API responses
- Malicious entries in `data/apis.json` (crafted URLs, injected markup)
- Script injection through API response data displayed in the browser
