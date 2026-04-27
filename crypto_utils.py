"""
crypto_utils.py
Fonctions cryptographiques utilisant OpenSSL en ligne de commande.
"""

import os
import subprocess
import hashlib
import tempfile


def chiffrer_fichier_aes(fichier_entree, fichier_sortie):
    """Chiffre un fichier avec AES-256-CBC. Retourne (cle, iv)."""
    cle = os.urandom(32)  # 256 bits
    iv  = os.urandom(16)  # 128 bits

    subprocess.run([
        "openssl", "enc", "-aes-256-cbc", "-nosalt",
        "-K",  cle.hex(),
        "-iv", iv.hex(),
        "-in",  fichier_entree,
        "-out", fichier_sortie
    ], check=True, capture_output=True)

    return cle, iv


def dechiffrer_fichier_aes(fichier_entree, fichier_sortie, cle, iv):
    """Déchiffre un fichier AES-256-CBC."""
    subprocess.run([
        "openssl", "enc", "-aes-256-cbc", "-d", "-nosalt",
        "-K",  cle.hex(),
        "-iv", iv.hex(),
        "-in",  fichier_entree,
        "-out", fichier_sortie
    ], check=True, capture_output=True)


def chiffrer_cle_rsa(cle, iv, chemin_cle_publique):
    """Chiffre (cle + iv) avec la clé publique RSA du serveur."""
    donnees = cle + iv  # 48 octets

    # Écrire dans un fichier temporaire
    tmp_entree = tempfile.mktemp(suffix=".bin")
    tmp_sortie = tempfile.mktemp(suffix=".enc")

    with open(tmp_entree, "wb") as f:
        f.write(donnees)

    subprocess.run([
        "openssl", "pkeyutl", "-encrypt", "-pubin",
        "-inkey", chemin_cle_publique,
        "-pkeyopt", "rsa_padding_mode:oaep",
        "-in",  tmp_entree,
        "-out", tmp_sortie
    ], check=True, capture_output=True)

    with open(tmp_sortie, "rb") as f:
        resultat = f.read()

    os.remove(tmp_entree)
    os.remove(tmp_sortie)
    return resultat


def dechiffrer_cle_rsa(donnees_chiffrees, chemin_cle_privee):
    """Déchiffre l'enveloppe RSA. Retourne (cle, iv)."""
    tmp_entree = tempfile.mktemp(suffix=".enc")
    tmp_sortie = tempfile.mktemp(suffix=".bin")

    with open(tmp_entree, "wb") as f:
        f.write(donnees_chiffrees)

    subprocess.run([
        "openssl", "pkeyutl", "-decrypt",
        "-inkey", chemin_cle_privee,
        "-pkeyopt", "rsa_padding_mode:oaep",
        "-in",  tmp_entree,
        "-out", tmp_sortie
    ], check=True, capture_output=True)

    with open(tmp_sortie, "rb") as f:
        donnees = f.read()

    os.remove(tmp_entree)
    os.remove(tmp_sortie)

    cle = donnees[:32]
    iv  = donnees[32:48]
    return cle, iv


def hash_sha256(fichier):
    """Calcule le hash SHA-256 d'un fichier."""
    h = hashlib.sha256()
    with open(fichier, "rb") as f:
        for bloc in iter(lambda: f.read(8192), b""):
            h.update(bloc)
    return h.digest()
