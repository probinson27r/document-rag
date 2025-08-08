# HTTPS Setup Guide for Localhost Development

This guide explains how to set up HTTPS for local development of the ED19024 application.

## Overview

HTTPS is essential for testing features that require secure connections, such as:
- Service Workers
- Web APIs that require HTTPS (camera, microphone, etc.)
- Testing authentication flows
- Ensuring your app works correctly in production-like conditions

## Prerequisites

### 1. Install OpenSSL

**macOS:**
```bash
brew install openssl
```

**Ubuntu/Debian:**
```bash
sudo apt-get install openssl
```

**Windows:**
Download from [https://slproweb.com/products/Win32OpenSSL.html](https://slproweb.com/products/Win32OpenSSL.html)

### 2. Verify Installation
```bash
openssl version
```

## Quick Start

### Option 1: Using the Convenience Script (Recommended)

```bash
./run_https.sh
```

This script will:
- Check if OpenSSL is installed
- Activate the virtual environment
- Set `DISABLE_AUTH=true`
- Generate SSL certificates if needed
- Start the HTTPS server

### Option 2: Manual Setup

1. **Generate SSL certificates:**
```bash
python generate_ssl_cert.py
```

2. **Run with HTTPS:**
```bash
DISABLE_AUTH=true python app.py --https
```

### Option 3: Custom Port

```bash
DISABLE_AUTH=true python app.py --https --port 8443
```

## SSL Certificate Details

### Certificate Location
- **Certificate:** `certs/localhost.crt`
- **Private Key:** `certs/localhost.key`

### Certificate Information
- **Type:** Self-signed certificate
- **Validity:** 365 days
- **Subject:** `/C=AU/ST=WA/L=Perth/O=Development/CN=localhost`
- **SAN (Subject Alternative Names):**
  - `localhost`
  - `*.localhost`
  - `127.0.0.1`
  - `::1`

### Regenerating Certificates
To regenerate certificates (e.g., if they expire):
```bash
rm -rf certs/
python generate_ssl_cert.py
```

## Browser Security Warnings

When you first access the HTTPS site, your browser will show a security warning because the certificate is self-signed. This is normal and expected.

### Chrome/Edge
1. Click "Advanced"
2. Click "Proceed to localhost (unsafe)"

### Firefox
1. Click "Advanced"
2. Click "Accept the Risk and Continue"

### Safari
1. Click "Show Details"
2. Click "visit this website"
3. Click "Visit Website" in the popup

## Command Line Options

The application supports several command line options:

```bash
python app.py [OPTIONS]

Options:
  --https              Run with HTTPS (requires SSL certificates)
  --port PORT          Port to run the server on (default: 5001)
  --host HOST          Host to bind to (default: 0.0.0.0)
  -h, --help           Show help message
```

### Examples

**HTTP (default):**
```bash
python app.py
```

**HTTPS on default port:**
```bash
python app.py --https
```

**HTTPS on custom port:**
```bash
python app.py --https --port 8443
```

**HTTPS on specific host:**
```bash
python app.py --https --host 127.0.0.1 --port 8443
```

## Troubleshooting

### Common Issues

1. **"OpenSSL not found"**
   - Install OpenSSL using the instructions above
   - Make sure it's in your PATH

2. **"Permission denied" on certificate generation**
   - Check file permissions in the `certs/` directory
   - Ensure you have write permissions

3. **"Certificate expired"**
   - Regenerate certificates: `rm -rf certs/ && python generate_ssl_cert.py`

4. **Browser still shows HTTP instead of HTTPS**
   - Clear browser cache
   - Make sure you're accessing `https://localhost:5001`
   - Check that the server started with HTTPS enabled

5. **"Connection refused"**
   - Check if the port is already in use
   - Try a different port: `python app.py --https --port 8443`

### Debug Mode

For debugging SSL issues, you can run with verbose output:

```bash
DISABLE_AUTH=true python app.py --https --debug
```

## Security Considerations

### Development Only
- These self-signed certificates are for **development only**
- Never use them in production
- The certificates are not trusted by browsers by default

### Certificate Security
- The private key is stored locally in `certs/localhost.key`
- Keep the `certs/` directory secure
- Don't commit certificates to version control (they're already in `.gitignore`)

### Production Deployment
For production, use:
- Proper SSL certificates from a trusted CA (Let's Encrypt, etc.)
- Reverse proxy (nginx, Apache) with SSL termination
- Cloud provider SSL services (AWS ALB, Cloudflare, etc.)

## Integration with Other Tools

### Docker Development
If you're using Docker for development, you'll need to:
1. Mount the `certs/` directory as a volume
2. Configure the container to use HTTPS
3. Update the Dockerfile to include OpenSSL

### CI/CD Pipeline
For automated testing with HTTPS:
1. Generate certificates in the CI environment
2. Configure test browsers to accept self-signed certificates
3. Use tools like `mkcert` for more trusted local certificates

## Advanced Configuration

### Custom Certificate Authority
For more trusted local certificates, consider using `mkcert`:

```bash
# Install mkcert
brew install mkcert  # macOS
mkcert -install

# Generate certificates
mkcert localhost 127.0.0.1 ::1

# Use the generated certificates
python app.py --https --cert localhost+2.pem --key localhost+2-key.pem
```

### Multiple Domains
To support multiple local domains, modify the certificate generation:

```bash
# Generate certificate for multiple domains
openssl req -new -x509 -keyout localhost.key -out localhost.crt -days 365 -subj "/CN=localhost" -addext "subjectAltName = DNS:localhost,DNS:*.localhost,DNS:dev.local,DNS:*.dev.local"
```

## Support

For issues with:
- **SSL Certificate Generation**: Check OpenSSL installation and permissions
- **Browser Security Warnings**: This is expected behavior for self-signed certificates
- **Application Integration**: Ensure the app is configured to use HTTPS endpoints
- **Production Deployment**: Use proper SSL certificates and reverse proxies

## References

- [Flask SSL Context Documentation](https://flask.palletsprojects.com/en/2.3.x/deploying/wsgi-standalone/#ssl-context)
- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [mkcert for Local HTTPS](https://github.com/FiloSottile/mkcert)
- [Let's Encrypt for Production](https://letsencrypt.org/) 