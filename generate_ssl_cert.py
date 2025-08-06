#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for localhost HTTPS development
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_ssl_cert():
    """Generate self-signed SSL certificate for localhost"""
    
    # Create certs directory if it doesn't exist
    certs_dir = Path("certs")
    certs_dir.mkdir(exist_ok=True)
    
    cert_file = certs_dir / "localhost.crt"
    key_file = certs_dir / "localhost.key"
    
    # Check if certificates already exist
    if cert_file.exists() and key_file.exists():
        print("✅ SSL certificates already exist")
        return str(cert_file), str(key_file)
    
    print("🔐 Generating self-signed SSL certificates for localhost...")
    
    try:
        # Generate private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(key_file), "2048"
        ], check=True, capture_output=True)
        
        # Generate certificate signing request
        csr_file = certs_dir / "localhost.csr"
        subprocess.run([
            "openssl", "req", "-new", "-key", str(key_file), "-out", str(csr_file),
            "-subj", "/C=AU/ST=WA/L=Perth/O=Development/CN=localhost"
        ], check=True, capture_output=True)
        
        # Generate self-signed certificate
        subprocess.run([
            "openssl", "x509", "-req", "-in", str(csr_file), "-signkey", str(key_file),
            "-out", str(cert_file), "-days", "365", "-extensions", "v3_req",
            "-extfile", "-"
        ], input=b"""
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
""", check=True, capture_output=True)
        
        # Clean up CSR file
        csr_file.unlink(missing_ok=True)
        
        print("✅ SSL certificates generated successfully!")
        print(f"   Certificate: {cert_file}")
        print(f"   Private Key: {key_file}")
        
        return str(cert_file), str(key_file)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificates: {e}")
        print("Make sure OpenSSL is installed on your system")
        return None, None
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL:")
        print("   macOS: brew install openssl")
        print("   Ubuntu/Debian: sudo apt-get install openssl")
        print("   Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        return None, None

if __name__ == "__main__":
    cert_file, key_file = generate_ssl_cert()
    if cert_file and key_file:
        print(f"\n🔗 To use HTTPS, run:")
        print(f"   python app.py --https")
        print(f"   or")
        print(f"   DISABLE_AUTH=true python app.py --https")
    else:
        sys.exit(1) 