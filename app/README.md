
### Enabling https for Phoenix

Based on [this documentation](https://arize.com/docs/phoenix/release-notes/04.2025/04.28.2025-tls-support-for-phoenix-server).

1. Get TLS/SSL certificate
   * (For Lightsail instance of Phoenix) Create and download certificate from ACM (AWS Certificate Manager)
      - Enable and copy static IP from Lightsail instance
      - Create A record static IP in Route 53
      - Request certificate in ACM
      - Created CNAME record based on request result for ACM to validate request
      - Upon ACM validation, exported certificate from ACM; download and move to a `certs` folder
      - Copy `certs` folder to Lightsail instance: `scp -i $SSH_KEY_PEM_FILE -r certs ec2-user@${STATIC_IP}`
   * (For local dev environment) Create self-signed certificate for Phoenix instance
```sh
# This 'certs' folder will be mounted as a volume in the phoenix Docker container
mkdir certs && cd certs
# Generate root CA's private key
openssl genrsa -out rootCA.key 4096
# Create self-signed root CA certificate
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3650 -out rootCA.crt -subj "/C=US/ST=Test/L=Test/O=DevRootCA/OU=IT/CN=DevRootCA"

# Generate a server's private key
openssl genrsa -out server.key 2048
# Create the server's certificate signing request (CSR)
# Important: include ALL possible hostnames in the subjectAltName list
# - "phoenix" for interactions between Docker containers within docker-compose network
# - "localhost" for connecting to Phoenix Docker container from outside the docker-compose network
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=Test/L=Test/O=MyTestServer/OU=IT/CN=phoenix" -addext "subjectAltName = DNS:phoenix,DNS:localhost"
# Sign CSR with the root CA certificate
# Important: use '-copy_extensions copy' to copy over subjectAltName values
openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out server.crt -days 825 -sha256 -copy_extensions copy
# Confirm alternative name
openssl x509 -in server.crt -noout -ext subjectAltName
# and other data
openssl x509 -in server.crt -noout -text
# Verify against root CA
openssl verify -CAfile rootCA.crt server.crt

# Include Root CA in server's cert so that it's available for client-side validation
cat server.crt rootCA.crt > server-fullchain.crt
```

2. Configure SSL in Phoenix by updating `compose.yaml` (locally or in Lightsail instance) with:
```yaml
    environment:
      ...
      - PHOENIX_TLS_ENABLED=True
      - PHOENIX_TLS_CERT_FILE=/certs/server-fullchain.crt
      - PHOENIX_TLS_KEY_FILE=/certs/server.key
      # - PHOENIX_TLS_KEY_FILE_PASSWORD=<insert password used when exporting certs from ACM>
      - PHOENIX_TLS_VERIFY_CLIENT=False
    volumes:
      - ./certs:/certs
```

3. Restart Phoenix

4. Update Phoenix client (i.e., Haystack backend)
   * In `local.env`, set `PHOENIX_COLLECTOR_ENDPOINT` to the secured Phoenix instance (i.e., `https` prefix)
   * (For Lightsail instance of Phoenix) Add Amazon's intermediate CA certificate by ensuring `certs/aws_ca_intermediate_cert` is set to the Amazon intermediate CA certificate.
     (Export the "Amazon RSA 2048 M04" intermediate certificate using a browser pointed at
  the Phoenix instance.)
   * (For local dev environment) Add self-signed root CA certificate as a trusted CA  by ensuring `certs/local_dev_only_selfsigned_ca_root_cert` is set to the self-signed root CA certificate.
     (Use the contents of `rootCA.crt` created in step 1 above.)

5. Restart Phoenix client
