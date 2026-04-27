"""
client.py
Client qui chiffre un fichier et l'envoie au serveur via TLS.

Utilisation : python client.py <fichier>
"""

import ssl
import socket
import struct
import os
import sys

from crypto_utils import chiffrer_fichier_aes, chiffrer_cle_rsa, hash_sha256

# Adresse du serveur
HOTE = "localhost"
PORT = 9443


def envoyer_fichier(chemin_fichier):
    nom_fichier = os.path.basename(chemin_fichier)
    print(f"\n=== Envoi de : {nom_fichier} ===")

    # ── Étape 1 : Hash SHA-256 du fichier original
    print("[1] Calcul du hash SHA-256...")
    hash_original = hash_sha256(chemin_fichier)
    print(f"    Hash : {hash_original.hex()}")

    # ── Étape 2 : Chiffrement AES-256
    print("[2] Chiffrement AES-256-CBC...")
    fichier_chiffre = chemin_fichier + ".aes"
    cle, iv = chiffrer_fichier_aes(chemin_fichier, fichier_chiffre)
    print(f"    Clé  : {cle.hex()}")
    print(f"    IV   : {iv.hex()}")

    # ── Étape 3 : Chiffrement RSA de la clé AES
    print("[3] Chiffrement RSA-OAEP de la clé AES...")
    cle_chiffree = chiffrer_cle_rsa(cle, iv, "pki/server/server_pub.pem")
    print(f"    Clé chiffrée : {len(cle_chiffree)} octets")

    # ── Étape 4 : Lire le fichier chiffré
    with open(fichier_chiffre, "rb") as f:
        donnees_chiffrees = f.read()
    os.remove(fichier_chiffre)  # nettoyer le fichier temporaire

    # ── Étape 5 : Construire le paquet à envoyer
    #    Format : [taille_cle(4o)] [cle_rsa] [hash(32o)]
    #             [taille_nom(2o)] [nom_fichier] [taille_données(8o)] [données_aes]
    nom_bytes = nom_fichier.encode()
    paquet  = struct.pack(">I", len(cle_chiffree)) + cle_chiffree
    paquet += hash_original
    paquet += struct.pack(">H", len(nom_bytes)) + nom_bytes
    paquet += struct.pack(">Q", len(donnees_chiffrees)) + donnees_chiffrees

    # ── Étape 6 : Connexion TLS et envoi
    print("[4] Connexion TLS au serveur...")
    contexte = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    contexte.minimum_version = ssl.TLSVersion.TLSv1_2
    contexte.load_verify_locations("pki/ca/ca.crt")  # vérifier le certificat serveur

    with socket.create_connection((HOTE, PORT)) as sock:
        with contexte.wrap_socket(sock, server_hostname=HOTE) as tls:
            print(f"    TLS établi — chiffrement : {tls.cipher()[0]}")

            # Envoyer la taille du paquet puis le paquet
            tls.sendall(struct.pack(">Q", len(paquet)))
            tls.sendall(paquet)
            print(f"[5] Paquet envoyé ({len(paquet)} octets)")

            # Lire la réponse du serveur
            reponse = tls.recv(256).decode()
            print(f"[6] Réponse serveur : {reponse}")

    print("=== Envoi terminé ===\n")


# ── Point d'entrée ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage : python client.py <fichier>")
        sys.exit(1)

    envoyer_fichier(sys.argv[1])
