"""
Client d'échange de fichiers sécurisé
Protocole :
  1. Connexion TLS avec certificat client (mTLS)
  2. Chiffrement AES-256-CBC du fichier à envoyer
  3. Enveloppe RSA (chiffrement clé AES avec clé publique serveur)
  4. Signature RSA-SHA256 du fichier chiffré
  5. Envoi du paquet sécurisé au serveur
"""
import ssl
import socket
import struct
import os
import sys
import tempfile
import logging
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from crypto_utils import (
    aes_encrypt_file, rsa_encrypt_key,
    sign_file, pack_secure_packet,
    sha256_file, verify_certificate, get_cert_info
)

#Config
HOST    = "localhost"
PORT    = 9443
PKI_DIR = Path("./pki")
BUFFER  = 4096

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("SecureClient")

def create_ssl_context() -> ssl.SSLContext:
    """
    Contexte SSL/TLS client avec mTLS.
    - Présente son certificat au serveur
    - Vérifie le certificat serveur via la CA
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    # Certificat client pour l'authentification mutuelle
    ctx.load_cert_chain(
        certfile=str(PKI_DIR / "client" / "client.crt"),
        keyfile =str(PKI_DIR / "client" / "client.key")
    )

    # Vérification du certificat serveur
    ctx.load_verify_locations(cafile=str(PKI_DIR / "ca" / "ca.crt"))
    ctx.verify_mode    = ssl.CERT_REQUIRED
    ctx.check_hostname = True
    return ctx

def send_all(sock: ssl.SSLSocket, data: bytes) -> None:
    """Envoie tous les octets, par blocs."""
    sent = 0
    while sent < len(data):
        n = sock.send(data[sent:sent+BUFFER])
        if n == 0:
            raise ConnectionError("Connexion rompue pendant l'envoi")
        sent += n


def encrypt_and_pack_file(file_path: str) -> tuple[bytes, dict]:
    """
    Chiffre le fichier et construit le paquet sécurisé.
    Retourne (paquet_bytes, infos_debug).
    """
    fname = os.path.basename(file_path)
    fsize = os.path.getsize(file_path)
    log.info(f"  Fichier source : {fname}  ({fsize:,} octets)")

    # ── Étape 1 : Hash SHA-256 original (intégrité)
    original_hash = sha256_file(file_path)
    log.info(f"  SHA-256 original : {original_hash.hex()[:32]}...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".aes") as tf:
        tmp_enc = tf.name

    try:
        #  Chiffrement AES-256-CBC
        aes_key, iv = aes_encrypt_file(file_path, tmp_enc)
        enc_size = os.path.getsize(tmp_enc)
        log.info(f"  ✔ AES-256-CBC : {enc_size:,} octets chiffrés")
        log.info(f"    Clé AES : {aes_key.hex()[:24]}...  IV : {iv.hex()}")

        #  Chiffrement RSA de (clé AES + IV)
        enc_key_iv = rsa_encrypt_key(
            aes_key, iv,
            str(PKI_DIR / "shared" / "server_pub.pem")
        )
        log.info(f"  ✔ RSA-OAEP : clé AES chiffrée ({len(enc_key_iv)} octets)")

        # Signature numérique RSA-SHA256 du fichier chiffré
        signature = sign_file(tmp_enc, str(PKI_DIR / "client" / "client.key"))
        log.info(f"  ✔ Signature RSA-SHA256 ({len(signature)} octets)")

        #Lecture du fichier chiffré
        with open(tmp_enc, "rb") as f:
            enc_file_bytes = f.read()

        # Assemblage du paquet
        packet = pack_secure_packet(
            enc_file_bytes, enc_key_iv,
            signature, original_hash, fname
        )

        infos = {
            "filename":     fname,
            "original_size": fsize,
            "encrypted_size": enc_size,
            "packet_size":   len(packet),
            "aes_key_hex":   aes_key.hex(),
            "iv_hex":        iv.hex(),
        }
        return packet, infos

    finally:
        if os.path.exists(tmp_enc):
            os.unlink(tmp_enc)


def send_file(file_path: str) -> bool:
    """Connecte, chiffre et envoie un fichier au serveur."""
    if not os.path.isfile(file_path):
        log.error(f"Fichier introuvable : {file_path}")
        return False

    log.info("━━━ Chiffrement du fichier ━━━")
    packet, infos = encrypt_and_pack_file(file_path)

    log.info("\n━━━ Connexion au serveur ━━━")
    ctx = create_ssl_context()

    try:
        with socket.create_connection((HOST, PORT), timeout=30) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=HOST) as tls_sock:
                # Afficher info certificat serveur
                server_cert = tls_sock.getpeercert()
                sv_subject  = dict(x[0] for x in server_cert.get("subject", []))
                log.info(f"  Serveur authentifié : CN={sv_subject.get('commonName')}")
                log.info(f"  Cipher TLS : {tls_sock.cipher()[0]}")

                # Envoyer commande
                tls_sock.send(b"SEND_FILE")
                ack = tls_sock.recv(16)
                if ack != b"READY":
                    log.error(f"Serveur non prêt : {ack}")
                    return False

                # Envoyer taille + paquet
                log.info(f"\n━━━ Envoi du paquet ({infos['packet_size']:,} octets) ━━━")
                send_all(tls_sock, struct.pack(">Q", len(packet)))
                send_all(tls_sock, packet)
                log.info("  ✔ Paquet envoyé")

                # Attendre confirmation
                resp = tls_sock.recv(256).decode()
                if resp.startswith("OK:"):
                    parts = resp.split(":")
                    log.info(f"  ✔ Serveur confirme : {parts[1]} ({parts[2]} octets)")
                    return True
                else:
                    log.error(f"  ✘ Serveur : {resp}")
                    return False

    except ssl.SSLCertVerificationError as e:
        log.error(f"Certificat serveur invalide : {e}")
    except ConnectionRefusedError:
        log.error(f"Connexion refusée — le serveur est-il démarré sur {HOST}:{PORT} ?")
    except Exception as e:
        log.error(f"Erreur : {e}")

    return False


def list_remote_files() -> None:
    """Liste les fichiers reçus par le serveur."""
    ctx = create_ssl_context()
    try:
        with socket.create_connection((HOST, PORT), timeout=10) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=HOST) as tls_sock:
                tls_sock.send(b"LIST_FILES")
                size_bytes = tls_sock.recv(4)
                size = struct.unpack(">I", size_bytes)[0]
                data = b""
                while len(data) < size:
                    data += tls_sock.recv(min(BUFFER, size - len(data)))
                print("\nFichiers reçus par le serveur :")
                print(data.decode())
    except Exception as e:
        log.error(f"Erreur listing : {e}")


def ping_server() -> bool:
    """Teste la connexion TLS avec le serveur."""
    ctx = create_ssl_context()
    try:
        with socket.create_connection((HOST, PORT), timeout=5) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=HOST) as tls_sock:
                tls_sock.send(b"PING")
                resp = tls_sock.recv(8)
                if resp == b"PONG":
                    log.info("✔ Serveur accessible (TLS OK)")
                    return True
    except Exception as e:
        log.error(f"Ping échoué : {e}")
    return False
# 
def print_usage():
    print("""
Usage :
  python3 client.py send <fichier>     — Envoyer un fichier
  python3 client.py list               — Lister les fichiers du serveur
  python3 client.py ping               — Tester la connexion
""")


def main():
    print("║   Client de Transfert Sécurisé   ║\n")
    if len(sys.argv) < 2:
        print_usage()
        return

    cmd = sys.argv[1]
    if cmd == "send" and len(sys.argv) == 3:
        ok = send_file(sys.argv[2])
        sys.exit(0 if ok else 1)
    elif cmd == "list":
        list_remote_files()
    elif cmd == "ping":
        ping_server()
    else:
        print_usage()


if __name__ == "__main__":
    main()
