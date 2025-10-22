
### Enabling https for Phoenix

Based on [this documentation](https://arize.com/docs/phoenix/release-notes/04.2025/04.28.2025-tls-support-for-phoenix-server).

1. Get TLS/SSL certificate
   * (For Lightsail instance of Phoenix) Create and download certificate from ACM (AWS Certificate Manager)
      - Enable and copy static IP from Lightsail instance
      - Create A record static IP in Route 53
      - Request certificate in ACM
      - Created CNAME record based on request result for ACM to validate request
      - Upon ACM validation, exported certificate from ACM; download and move to a `certs` folder
      - Append the contents of `certificate_chain.txt` to the end of `certificate.pem`
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


### Enabling authentication in Phoenix

Based on [documentation](https://arize.com/docs/phoenix/self-hosting/features/authentication), set `PHOENIX_SECRET` in `docker-compose.yaml` as follows.
* Add these environment variables to the `phoenix` service:
```
      - PHOENIX_ENABLE_AUTH=True
      - PHOENIX_SECRET=SomeLongSecretThatIsUsedToSignJWTsForTheDeployment
```
* Restart and log into the Phoenix UI at http://localhost:6006 and create a system API key; copy the API key
* Add PHOENIX_API_KEY environment variable in `override.env` for the Haystack service to authenticate to Phoenix:
```
      - PHOENIX_API_KEY=<paste API key>
```

### Copying prompts from the deployed Phoenix

For local development, you'll likely want to replicate the prompts in the deployed Phoenix instance onto your local Phoenix instance.
To do so, add the `DEPLOYED_PHOENIX_URL` and `DEPLOYED_PHOENIX_API_KEY` environment variables to `override.env`.
Create a system API key at `$DEPLOYED_PHOENIX_URL/settings/general`.
Then run `make copy-prompts`. This will copy the prompt versions specified in `app_config.py`, which are the ones used in the deployed app.
Remember to do this every time the prompt version is updated in `app_config.py`. When running locally, the latest version of the prompt is used.


### Enabling OpenAI - aka ChatGPT - for generate action plan

Go to 1Password and retrieve "OpenAI API Key"

* Add OPENAI_API_KEY environment variable in `override.env` to allow the app to connect to OpenAI:
```
      - OPENAI_API_KEY=<paste API key>
```