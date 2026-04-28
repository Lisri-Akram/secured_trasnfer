#!/bin/bash
# setup_pki.sh — PKI simplifiée : CA + Certificat Serveur uniquement
set -e

PKI_DIR="./pki"
mkdir -p "$PKI_DIR"/{ca,server}

echo "[1/3] Génération clé CA (RSA 2048 bits)..."
openssl genrsa -out "$PKI_DIR/ca/ca.key" 2048

MSYS2_ARG_CONV_EXCL='*' openssl req -new -x509 -days 3650 \
    -key "$PKI_DIR/ca/ca.key" \
    -out "$PKI_DIR/ca/ca.crt" \
    -subj "/C=DZ/ST=Algiers/O=USTHB Computer Science Faculty/CN=SimpleCA"
echo "  ✔ CA créée (valide 10 ans)"

echo "[2/3] Génération certificat serveur (RSA 2048 bits)..."
openssl genrsa -out "$PKI_DIR/server/server.key" 2048

MSYS2_ARG_CONV_EXCL='*' openssl req -new \
    -key "$PKI_DIR/server/server.key" \
    -out "$PKI_DIR/server/server.csr" \
    -subj "/C=DZ/ST=Algiers/O=SecureTransfer/CN=localhost"

cat > "$PKI_DIR/server/ext.cnf" <<EOF
[v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = localhost
IP.1  = 127.0.0.1
EOF

openssl x509 -req -days 365 \
    -in     "$PKI_DIR/server/server.csr" \
    -CA     "$PKI_DIR/ca/ca.crt" \
    -CAkey  "$PKI_DIR/ca/ca.key" \
    -CAcreateserial \
    -extfile "$PKI_DIR/server/ext.cnf" \
    -extensions v3_req \
    -out "$PKI_DIR/server/server.crt"
echo "  ✔ Certificat serveur signé par la CA"

echo "[3/3] Extraction clé publique RSA du serveur..."
openssl x509 -pubkey -noout \
    -in  "$PKI_DIR/server/server.crt" \
    -out "$PKI_DIR/server/server_pub.pem"
echo "  ✔ Clé publique exportée → server_pub.pem"

echo ""
echo "✔ PKI prête !"
echo "  pki/ca/ca.crt              → Certificat CA (à fournir au client)"
echo "  pki/server/server.crt/.key → Certificat + clé privée du serveur"
echo "  pki/server/server_pub.pem  → Clé publique RSA (pour chiffrer la clé AES)"
echo ""
openssl verify -CAfile "$PKI_DIR/ca/ca.crt" "$PKI_DIR/server/server.crt"
