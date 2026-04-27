"""
server.py
Serveur qui reçoit un fichier chiffré, le déchiffre et le sauvegarde.

Utilisation : python server.py
"""

import ssl
import socket
import struct
import os
import tempfile
from datetime import datetime

from crypto_utils import dechiffrer_cle_rsa, dechiffrer_fichier_aes, hash_sha256

# Configuration serveur
HOTE     = "0.0.0.0"
PORT     = 9443
DOSSIER  = "received_files"   # dossier où sauvegarder les fichiers reçus


def recevoir_donnees(sock, n):
    """Reçoit exactement n octets depuis le socket."""
    donnees = b""
    while len(donnees) < n:
        bloc = sock.recv(min(4096, n - len(donnees)))
        if not bloc:
            raise ConnectionError("Connexion interrompue")
        donnees += bloc
    return donnees


def traiter_client(connexion, adresse):
    """Reçoit, déchiffre et sauvegarde le fichier envoyé par le client."""
    print(f"\n=== Nouvelle connexion : {adresse[0]}:{adresse[1]} ===")
    try:
        # ── Étape 1 : Lire la taille du paquet puis le paquet
        taille_totale = struct.unpack(">Q", recevoir_donnees(connexion, 8))[0]
        print(f"[1] Réception du paquet ({taille_totale} octets)...")
        paquet = recevoir_donnees(connexion, taille_totale)

        # ── Étape 2 : Désassembler le paquet
        offset = 0

        # Clé AES chiffrée RSA
        taille_cle = struct.unpack_from(">I", paquet, offset)[0]; offset += 4
        cle_chiffree = paquet[offset:offset + taille_cle];         offset += taille_cle

        # Hash SHA-256 original
        hash_original = paquet[offset:offset + 32];                offset += 32

        # Nom du fichier
        taille_nom = struct.unpack_from(">H", paquet, offset)[0];  offset += 2
        nom_fichier = paquet[offset:offset + taille_nom].decode(); offset += taille_nom

        # Données chiffrées
        taille_donnees = struct.unpack_from(">Q", paquet, offset)[0]; offset += 8
        donnees_chiffrees = paquet[offset:offset + taille_donnees]

        print(f"[2] Fichier reçu : {nom_fichier}")

        # ── Étape 3 : Déchiffrer la clé AES avec la clé privée RSA
        print("[3] Déchiffrement RSA-OAEP de la clé AES...")
        cle, iv = dechiffrer_cle_rsa(cle_chiffree, "pki/server/server.key")
        print(f"    Clé : {cle.hex()}")
        print(f"    IV  : {iv.hex()}")

        # ── Étape 4 : Déchiffrer le fichier avec AES
        print("[4] Déchiffrement AES-256-CBC du fichier...")
        os.makedirs(DOSSIER, exist_ok=True)

        # Écrire les données chiffrées dans un fichier temporaire
        tmp = tempfile.mktemp(suffix=".aes")
        with open(tmp, "wb") as f:
            f.write(donnees_chiffrees)

        # Déchiffrer vers le fichier de sortie
        horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
        chemin_sortie = os.path.join(DOSSIER, f"{horodatage}_{nom_fichier}")
        dechiffrer_fichier_aes(tmp, chemin_sortie, cle, iv)
        os.remove(tmp)
        print(f"    Fichier sauvegardé : {chemin_sortie}")

        # ── Étape 5 : Vérifier l'intégrité SHA-256
        print("[5] Vérification du hash SHA-256...")
        hash_recu = hash_sha256(chemin_sortie)
        if hash_recu == hash_original:
            print("    ✔ Intégrité vérifiée — fichier intact")
            connexion.send(b"OK : fichier recu et verifie")
        else:
            print("    ✘ Hash différent — fichier corrompu !")
            connexion.send(b"ERREUR : hash incorrect")

    except Exception as e:
        print(f"Erreur : {e}")
        try:
            connexion.send(b"ERREUR")
        except Exception:
            pass
    finally:
        connexion.close()
        print("=== Connexion fermée ===")


# ── Point d'entrée ─────────────────────────────────────────────
if __name__ == "__main__":
    # Créer le contexte TLS serveur
    contexte = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexte.minimum_version = ssl.TLSVersion.TLSv1_2
    contexte.load_cert_chain(
        certfile="pki/server/server.crt",   # certificat X.509
        keyfile ="pki/server/server.key"    # clé privée RSA
    )

    os.makedirs(DOSSIER, exist_ok=True)
    print(f"Serveur TLS démarré sur le port {PORT}")
    print("En attente de connexions...\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock_brut:
        sock_brut.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_brut.bind((HOTE, PORT))
        sock_brut.listen(5)

        with contexte.wrap_socket(sock_brut, server_side=True) as sock_tls:
            while True:
                try:
                    connexion, adresse = sock_tls.accept()
                    traiter_client(connexion, adresse)
                except ssl.SSLError as e:
                    print(f"Erreur TLS : {e}")
                except KeyboardInterrupt:
                    print("\nServeur arrêté.")
                    break
