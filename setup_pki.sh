# setup_pki.sh — Infrastructure PKI 
# Génère : CA root, certificat serveur, certificat client
set -e
BOLD="\e[1m"; GREEN="\e[32m"; CYAN="\e[36m"; YELLOW="\e[33m"; RESET="\e[0m"
echo -e "${BOLD}${CYAN}║Configuration PKI — Échange Sécurisé║${RESET}"
PKI_DIR="./pki"
mkdir -p "$PKI_DIR"/{ca,server,client,shared}
# AUTORITÉ DE CERTIFICATION
echo -e "\n${BOLD}${YELLOW}[1/6] Génération de la clé privée CA (RSA 4096 bits)...${RESET}"
openssl genrsa -aes256 -passout pass:ca_secret_2024 \
    -out "$PKI_DIR/ca/ca.key" 4096
echo -e "${GREEN}✔ Clé CA générée${RESET}"

echo -e "${BOLD}${YELLOW}[2/6] Création du certificat racine CA (auto-signé, 10 ans)...${RESET}"
MSYS2_ARG_CONV_EXCL='*' openssl req -new -x509 -days 3650 \
    -key "$PKI_DIR/ca/ca.key" \
    -passin pass:ca_secret_2024 \
    -out "$PKI_DIR/ca/ca.crt" \
    -subj "/C=DZ/ST=Blida/L=Blida/O=Universite Saad Dahleb/OU=Departement Informatique/CN=SecureTransfer-CA"
echo -e "${GREEN}✔ Certificat CA créé${RESET}"
#  CERTIFICAT SERVEUR
echo -e "\n${BOLD}${YELLOW}[3/6] Génération certificat SERVEUR...${RESET}"
openssl genrsa -out "$PKI_DIR/server/server.key" 2048

MSYS2_ARG_CONV_EXCL='*' openssl req -new \
    -key "$PKI_DIR/server/server.key" \
    -out "$PKI_DIR/server/server.csr" \
    -subj "/C=DZ/ST=Blida/O=SecureTransfer/CN=localhost"
# Extension SAN (Subject Alternative Name)
cat > "$PKI_DIR/server/server_ext.cnf" <<EOF
[v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = localhost
IP.1  = 127.0.0.1
EOF

openssl x509 -req -days 365 \
    -in  "$PKI_DIR/server/server.csr" \
    -CA  "$PKI_DIR/ca/ca.crt" \
    -CAkey "$PKI_DIR/ca/ca.key" \
    -passin pass:ca_secret_2024 \
    -CAcreateserial \
    -extfile "$PKI_DIR/server/server_ext.cnf" \
    -extensions v3_req \
    -out "$PKI_DIR/server/server.crt"
echo -e "${GREEN}✔ Certificat serveur signé par la CA${RESET}"
#CERTIFICAT CLIENT
echo -e "\n${BOLD}${YELLOW}[4/6] Génération certificat CLIENT...${RESET}"
openssl genrsa -out "$PKI_DIR/client/client.key" 2048

MSYS2_ARG_CONV_EXCL='*' openssl req -new \
    -key "$PKI_DIR/client/client.key" \
    -out "$PKI_DIR/client/client.csr" \
    -subj "/C=DZ/ST=Blida/O=SecureTransfer/CN=client01"

openssl x509 -req -days 365 \
    -in  "$PKI_DIR/client/client.csr" \
    -CA  "$PKI_DIR/ca/ca.crt" \
    -CAkey "$PKI_DIR/ca/ca.key" \
    -passin pass:ca_secret_2024 \
    -CAcreateserial \
    -out "$PKI_DIR/client/client.crt"
echo -e "${GREEN}✔ Certificat client signé par la CA${RESET}"
#EXTRACTION DES CLÉS PUBLIQUES RSA
echo -e "\n${BOLD}${YELLOW}[5/6] Extraction des clés publiques RSA...${RESET}"
openssl x509 -pubkey -noout \
    -in "$PKI_DIR/server/server.crt" \
    -out "$PKI_DIR/server/server_pub.pem"

openssl x509 -pubkey -noout \
    -in "$PKI_DIR/client/client.crt" \
    -out "$PKI_DIR/client/client_pub.pem"

# Copie des clés publiques dans shared/ (échange préalable simulé)
cp "$PKI_DIR/server/server_pub.pem" "$PKI_DIR/shared/"
cp "$PKI_DIR/client/client_pub.pem" "$PKI_DIR/shared/"
cp "$PKI_DIR/ca/ca.crt"            "$PKI_DIR/shared/"
echo -e "${GREEN}✔ Clés publiques exportées vers shared/${RESET}"
#  RÉSUMÉ
echo -e "\n${BOLD}${YELLOW}[6/6] Vérification des certificats...${RESET}"
echo -e "${CYAN}--- Certificat SERVEUR ---${RESET}"
openssl verify -CAfile "$PKI_DIR/ca/ca.crt" "$PKI_DIR/server/server.crt"
echo -e "${CYAN}--- Certificat CLIENT  ---${RESET}"
openssl verify -CAfile "$PKI_DIR/ca/ca.crt" "$PKI_DIR/client/client.crt"
echo -e "${BOLD}${GREEN}║PKI configurée avec succès║${RESET}"
echo -e "Structure :"
find "$PKI_DIR" -type f | sort | sed 's/^/  /'
