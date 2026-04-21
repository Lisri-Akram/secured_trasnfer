"""
crypto_utils.py — Utilitaires de chiffrement via OpenSSL
=========================================================
Protocole d'échange sécurisé :
  1. Générer une clé AES-256 aléatoire (clé de session)
  2. Chiffrer le fichier avec AES-256-CBC + IV aléatoire
  3. Chiffrer la clé AES avec la clé publique RSA du destinataire
  4. Signer le paquet avec la clé privée de l'expéditeur
  5. Envoyer : [signature | clé_AES_chiffrée | IV | fichier_chiffré]
"""

import os
import subprocess
import struct
import hashlib
import tempfile
from pathlib import Path
# CHIFFREMENT AES-256-CBC (via OpenSSL CLI)
def aes_encrypt_file(input_path: str, output_path: str) -> tuple[bytes, bytes]:
    """
    Chiffre un fichier avec AES-256-CBC.
    Retourne (aes_key_hex, iv_hex) — 32 octets chacun.
    """
    # Génération clé AES et IV aléatoires (256 bits)
    aes_key = os.urandom(32)
    iv      = os.urandom(16)

    result = subprocess.run([
        "openssl", "enc", "-aes-256-cbc",
        "-K",  aes_key.hex(),
        "-iv", iv.hex(),
        "-in",  input_path,
        "-out", output_path,
        "-nosalt"
    ], capture_output=True)

    if result.returncode != 0:
        raise RuntimeError(f"AES encrypt failed: {result.stderr.decode()}")

    return aes_key, iv


def aes_decrypt_file(input_path: str, output_path: str,
                     aes_key: bytes, iv: bytes) -> None:
    """
    Déchiffre un fichier AES-256-CBC avec la clé et l'IV fournis.
    """
    result = subprocess.run([
        "openssl", "enc", "-aes-256-cbc", "-d",
        "-K",  aes_key.hex(),
        "-iv", iv.hex(),
        "-in",  input_path,
        "-out", output_path,
        "-nosalt"
    ], capture_output=True)

    if result.returncode != 0:
        raise RuntimeError(f"AES decrypt failed: {result.stderr.decode()}")
# CHIFFREMENT RSA (enveloppe numérique pour la clé AES)
def rsa_encrypt_key(aes_key: bytes, iv: bytes,
                    recipient_pubkey_path: str) -> bytes:
    """
    Chiffre (aes_key || iv) avec la clé publique RSA du destinataire.
    Utilise OAEP padding (plus sécurisé que PKCS#1 v1.5).
    Retourne les octets chiffrés.
    """
    plain_data = aes_key + iv# 32 + 16 = 48 octets

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tf:
        tf.write(plain_data)
        tmp_in = tf.name

    tmp_out = tmp_in + ".enc"
    try:
        result = subprocess.run([
            "openssl", "rsautl",
            "-encrypt",
            "-oaep",
            "-pubin",
            "-inkey", recipient_pubkey_path,
            "-in",  tmp_in,
            "-out", tmp_out
        ], capture_output=True)

        if result.returncode != 0:
            raise RuntimeError(f"RSA encrypt failed: {result.stderr.decode()}")

        with open(tmp_out, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_in)
        if os.path.exists(tmp_out):
            os.unlink(tmp_out)


def rsa_decrypt_key(encrypted_key_iv: bytes,
                    private_key_path: str) -> tuple[bytes, bytes]:
    """
    Déchiffre l'enveloppe RSA pour récupérer (aes_key, iv).
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as tf:
        tf.write(encrypted_key_iv)
        tmp_in = tf.name

    tmp_out = tmp_in + ".dec"
    try:
        result = subprocess.run([
            "openssl", "rsautl",
            "-decrypt",
            "-oaep",
            "-inkey", private_key_path,
            "-in",  tmp_in,
            "-out", tmp_out
        ], capture_output=True)

        if result.returncode != 0:
            raise RuntimeError(f"RSA decrypt failed: {result.stderr.decode()}")

        with open(tmp_out, "rb") as f:
            plain = f.read()

        aes_key = plain[:32]
        iv      = plain[32:48]
        return aes_key, iv
    finally:
        os.unlink(tmp_in)
        if os.path.exists(tmp_out):
            os.unlink(tmp_out)
# SIGNATURE NUMÉRIQUE RSA-SHA256
def sign_file(file_path: str, private_key_path: str) -> bytes:
    """
    Signe le hash SHA-256 du fichier avec la clé privée RSA.
    Retourne la signature DER (octets).
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sig") as tf:
        tmp_sig = tf.name

    try:
        result = subprocess.run([
            "openssl", "dgst", "-sha256",
            "-sign", private_key_path,
            "-out",  tmp_sig,
            file_path
        ], capture_output=True)

        if result.returncode != 0:
            raise RuntimeError(f"Sign failed: {result.stderr.decode()}")

        with open(tmp_sig, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_sig):
            os.unlink(tmp_sig)


def verify_signature(file_path: str, signature: bytes,
                     sender_cert_or_pubkey_path: str) -> bool:
    """
    Vérifie la signature RSA-SHA256.
    Accepte un certificat (.crt) ou une clé publique (.pem).
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sig") as tf:
        tf.write(signature)
        tmp_sig = tf.name

    try:
        # Déterminer si c'est un certificat ou une clé publique
        ext = Path(sender_cert_or_pubkey_path).suffix
        if ext == ".crt":
            # Extraire la clé publique du certificat
            tmp_pub = tmp_sig + ".pub"
            subprocess.run([
                "openssl", "x509", "-pubkey", "-noout",
                "-in", sender_cert_or_pubkey_path,
                "-out", tmp_pub
            ], check=True, capture_output=True)
            pubkey_path = tmp_pub
        else:
            pubkey_path = sender_cert_or_pubkey_path
            tmp_pub = None

        result = subprocess.run([
            "openssl", "dgst", "-sha256",
            "-verify", pubkey_path,
            "-signature", tmp_sig,
            file_path
        ], capture_output=True)

        return result.returncode == 0
    finally:
        os.unlink(tmp_sig)
        if 'tmp_pub' in locals() and tmp_pub and os.path.exists(tmp_pub):
            os.unlink(tmp_pub)
# VÉRIFICATION CERTIFICAT X.509
def verify_certificate(cert_path: str, ca_cert_path: str) -> bool:
    """Vérifie qu'un certificat a bien été signé par la CA."""
    result = subprocess.run([
        "openssl", "verify",
        "-CAfile", ca_cert_path,
        cert_path
    ], capture_output=True)
    return result.returncode == 0


def get_cert_info(cert_path: str) -> dict:
    """Extrait les informations d'un certificat X.509."""
    result = subprocess.run([
        "openssl", "x509", "-noout",
        "-subject", "-issuer", "-dates", "-serial",
        "-in", cert_path
    ], capture_output=True, text=True)
    info = {}
    for line in result.stdout.strip().splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            info[k.strip()] = v.strip()
    return info
# EMBALLAGE/DÉBALLAGE DU PAQUET SÉCURISÉ

# Format du paquet binaire :
#MAGIC (4B) │ VERSION (1B) │ ...champs longueur/données  
#sig_len (4B) │ signature (sig_len B)                    
#enc_key_len (4B) │ clé AES chiffrée RSA (enc_key_len B) 
#filename_len (2B) │ nom de fichier (filename_len B)      
#file_size (8B) │ fichier chiffré AES (file_size B)       
#sha256_hash (32B) — hash du fichier original             


MAGIC   = b"STFX"   # Secure Transfer File eXchange
VERSION = 1


def pack_secure_packet(encrypted_file_bytes: bytes,
                       encrypted_aes_key_iv: bytes,
                       signature: bytes,
                       original_hash: bytes,
                       filename: str) -> bytes:
    """Assemble le paquet sécurisé complet."""
    fname_bytes = filename.encode("utf-8")
    packet  = MAGIC
    packet += struct.pack("B",  VERSION)
    packet += struct.pack(">I", len(signature))         + signature
    packet += struct.pack(">I", len(encrypted_aes_key_iv)) + encrypted_aes_key_iv
    packet += struct.pack(">H", len(fname_bytes))       + fname_bytes
    packet += struct.pack(">Q", len(encrypted_file_bytes)) + encrypted_file_bytes
    packet += original_hash   # 32 octets SHA-256
    return packet


def unpack_secure_packet(data: bytes) -> dict:
    """Désassemble et valide le paquet sécurisé."""
    if data[:4] != MAGIC:
        raise ValueError("Paquet invalide : MAGIC incorrect")

    offset = 4
    version = struct.unpack_from("B", data, offset)[0]; offset += 1

    sig_len = struct.unpack_from(">I", data, offset)[0]; offset += 4
    signature = data[offset:offset+sig_len]; offset += sig_len

    key_len = struct.unpack_from(">I", data, offset)[0]; offset += 4
    enc_key_iv = data[offset:offset+key_len]; offset += key_len

    fname_len = struct.unpack_from(">H", data, offset)[0]; offset += 2
    filename = data[offset:offset+fname_len].decode("utf-8"); offset += fname_len

    file_size = struct.unpack_from(">Q", data, offset)[0]; offset += 8
    enc_file  = data[offset:offset+file_size]; offset += file_size

    original_hash = data[offset:offset+32]

    return {
        "version":   version,
        "signature": signature,
        "enc_key_iv": enc_key_iv,
        "filename":  filename,
        "enc_file":  enc_file,
        "original_hash": original_hash
    }


def sha256_file(path: str) -> bytes:
    """Calcule le hash SHA-256 d'un fichier."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.digest()
