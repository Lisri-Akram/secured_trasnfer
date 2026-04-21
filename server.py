"""
server.py — Serveur d'échange de fichiers sécurisé
Protocole :
  • TLS mutual (mTLS) — authentification client + serveur par certificats
  • Réception de fichiers chiffrés AES + enveloppe RSA
  • Vérification de signature numérique de l'expéditeur
  • Déchiffrement et stockage des fichiers reçus
"""

import ssl
import socket
import struct
import os
import sys
import tempfile
import hashlib
import logging
from pathlib import Path
from datetime import datetime

# Import utils crypto
sys.path.insert(0, os.path.dirname(__file__))
from crypto_utils import (
    rsa_decrypt_key, aes_decrypt_file,
    verify_signature, verify_certificate,
    get_cert_info, unpack_secure_packet, sha256_file
)

# ── Config
HOST       = "0.0.0.0"
PORT       = 9443
PKI_DIR    = Path("./pki")
RECV_DIR   = Path("./received_files")
BUFFER     = 4096

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("SecureServer")


# ══════════════════════════════════════════════════════════════
def create_ssl_context() -> ssl.SSLContext:
    """
    Crée le contexte SSL/TLS serveur avec mTLS.
    - Certificat serveur signé par la CA
    - Exige un certificat client valide (CERT_REQUIRED)
    - TLS 1.2 minimum
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    # Chargement certificat + clé privée du serveur
    ctx.load_cert_chain(
        certfile=str(PKI_DIR / "server" / "server.crt"),
        keyfile =str(PKI_DIR / "server" / "server.key")
    )

    # Exiger l'authentification mutuelle (mTLS)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile=str(PKI_DIR / "ca" / "ca.crt"))

    # Désactiver les suites de chiffrement faibles
    ctx.set_ciphers(
        "ECDHE-RSA-AES256-GCM-SHA384:"
        "ECDHE-RSA-AES128-GCM-SHA256:"
        "DHE-RSA-AES256-GCM-SHA384"
    )
    return ctx


# ══════════════════════════════════════════════════════════════
def recv_all(sock: ssl.SSLSocket, n: int) -> bytes:
    """Reçoit exactement n octets depuis le socket."""
    data = b""
    while len(data) < n:
        chunk = sock.recv(min(BUFFER, n - len(data)))
        if not chunk:
            raise ConnectionError("Connexion fermée prématurément")
        data += chunk
    return data


def receive_file_packet(conn: ssl.SSLSocket) -> bytes:
    """
    Protocole de réception :
    [taille_paquet (8B)] [paquet_securise (...)]
    """
    size_bytes = recv_all(conn, 8)
    total_size = struct.unpack(">Q", size_bytes)[0]

    log.info(f"  Réception paquet : {total_size:,} octets")
    packet_data = recv_all(conn, total_size)
    return packet_data

def process_packet(packet_data: bytes, client_cn: str) -> str | None:
    """
    Déchiffre et vérifie un paquet sécurisé reçu.
    Retourne le chemin du fichier déchiffré, ou None si erreur.
    """
    # 1. Désassemblement du paquet
    pkt = unpack_secure_packet(packet_data)
    filename = pkt["filename"]
    log.info(f"  Fichier : {filename}")

    # 2. Vérification de la signature numérique
    client_pubkey = PKI_DIR / "shared" / "client_pub.pem"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as tf:
        tf.write(pkt["enc_file"])
        tmp_enc = tf.name

    try:
        sig_ok = verify_signature(tmp_enc, pkt["signature"],
                                  str(client_pubkey))
        if not sig_ok:
            log.error("  ✘ SIGNATURE INVALIDE — paquet rejeté")
            return None
        log.info("  ✔ Signature vérifiée")

        # 3. Déchiffrement RSA de la clé AES
        aes_key, iv = rsa_decrypt_key(
            pkt["enc_key_iv"],
            str(PKI_DIR / "server" / "server.key")
        )
        log.info("  ✔ Clé AES déchiffrée (RSA-OAEP)")

        # 4. Déchiffrement AES-256-CBC du fichier
        RECV_DIR.mkdir(parents=True, exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = str(RECV_DIR / f"{ts}_{filename}")

        aes_decrypt_file(tmp_enc, out_path, aes_key, iv)
        log.info(f"  ✔ Fichier déchiffré : {out_path}")

        # 5. Vérification intégrité SHA-256
        computed = sha256_file(out_path)
        if computed == pkt["original_hash"]:
            log.info("  ✔ Intégrité SHA-256 vérifiée")
        else:
            log.warning("  ⚠ Hash SHA-256 différent — fichier possiblement altéré")

        return out_path

    finally:
        os.unlink(tmp_enc)
#
def handle_client(conn: ssl.SSLSocket, addr: tuple) -> None:
    """Gère une connexion client."""
    log.info(f"━━━ Connexion de {addr[0]}:{addr[1]}")

    # Récupérer le CN du certificat client
    cert = conn.getpeercert()
    subject = dict(x[0] for x in cert.get("subject", []))
    cn = subject.get("commonName", "inconnu")
    log.info(f"  Client authentifié : CN={cn}")

    try:
        # Attente des commandes
        cmd = conn.recv(16).decode().strip()
        log.info(f"  Commande : {cmd}")

        if cmd == "SEND_FILE":
            conn.send(b"READY")
            packet = receive_file_packet(conn)

            out_path = process_packet(packet, cn)
            if out_path:
                size = os.path.getsize(out_path)
                conn.send(f"OK:{os.path.basename(out_path)}:{size}".encode())
                log.info(f"  ✔ Transfert réussi → {out_path}")
            else:
                conn.send(b"ERR:VERIFICATION_FAILED")

        elif cmd == "LIST_FILES":
            files = list(RECV_DIR.glob("*")) if RECV_DIR.exists() else []
            listing = "\n".join(f.name for f in files) or "(aucun fichier)"
            data = listing.encode()
            conn.send(struct.pack(">I", len(data)) + data)

        elif cmd == "PING":
            conn.send(b"PONG")

        else:
            conn.send(b"ERR:UNKNOWN_CMD")

    except Exception as e:
        log.error(f"  Erreur client : {e}")
    finally:
        conn.close()
        log.info(f"  Connexion fermée ({addr[0]})")


# ══════════════════════════════════════════════════════════════
def main():
    log.info("║   Serveur de Transfert Sécurisé    ║")
    ctx = create_ssl_context()
    RECV_DIR.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
        raw_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw_sock.bind((HOST, PORT))
        raw_sock.listen(5)
        log.info(f"Écoute sur {HOST}:{PORT} (TLS 1.2+, mTLS activé)")
        log.info("Attente de connexions clients...\n")

        with ctx.wrap_socket(raw_sock, server_side=True) as tls_sock:
            while True:
                try:
                    conn, addr = tls_sock.accept()
                    handle_client(conn, addr)
                except ssl.SSLError as e:
                    log.warning(f"Erreur TLS : {e}")
                except KeyboardInterrupt:
                    log.info("\nArrêt du serveur.")
                    break


if __name__ == "__main__":
    main()
