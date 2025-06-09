#!/bin/bash
set -ex
pushd /etc/rabbitmq/certs

# Generate a private key for the CA.
openssl genpkey -pass=pass: -algorithm RSA -out ca_key.pem -aes256

# Generate a CA certificate.
echo -e "\n\n\n\n\n\n\n" |\
  openssl req -passin=pass: -x509 -new -nodes -key ca_key.pem -sha256 \
	  -days 1 -out ca_certificate.pem

# Generate a private key for the server.
openssl genpkey -pass=pass: -algorithm RSA -out server_key.pem

# Create a Certificate Signing Request (CSR) for the server certificate.
echo -e "\n\n\n\n\n\n\n\n\n" |\
  openssl req -new -key server_key.pem -out server_csr.pem

# Sign the server certificate with the CA.
openssl x509 -passin=pass: -req -in server_csr.pem -CA ca_certificate.pem \
	-CAkey ca_key.pem -CAcreateserial -out server_certificate.pem \
	-days 1 -sha256

# Remove the files we don't need.
rm -f ca_key.pem ca_certificate.srl server_csr.pem

popd
exec rabbitmq-server "$@"
