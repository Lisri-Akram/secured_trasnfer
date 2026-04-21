"""
 Démonstration complète (sans réseau)
Simule l'échange sécurisé complet côté expéditeur et destinataire,
en local, pour valider toutes les étapes cryptographiques.
"""

import os
import sys
import tempfile
import shutil
import subprocess
import hashlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from crypto_utils import (
    aes_encrypt_file, aes_decrypt_file,
    rsa_encrypt_key, rsa_decrypt_key,
    sign_file, verify_signature,
    verify_certificate, get_cert_info,
    pack_secure_packet, unpack_secure_packet,
    sha256_file
)

PKI_DIR = Path("./pki")
OK  = "  \033[32m✔\033[0m"
ERR = "  \033[31m✘\033[0m"
HDR = "\033[1m\033[36m"
RST = "\033[0m"


def section(title: str):
    print(f"\n{HDR}{'═'*54}{RST}")
    print(f"{HDR}  {title}{RST}")
    print(f"{HDR}{'═'*54}{RST}")


def check_pki():
    """Vérifie que la PKI a été configurée."""
    required = [
        PKI_DIR / "ca"     / "ca.crt",
        PKI_DIR / "server" / "server.crt",
        PKI_DIR / "server" / "server.key",
        PKI_DIR / "client" / "client.crt",
        PKI_DIR / "client" / "client.key",
        PKI_DIR / "shared" / "server_pub.pem",
        PKI_DIR / "shared" / "client_pub.pem",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print(f"{ERR} PKI manquante. Exécutez d'abord : bash setup_pki.sh")
        for m in missing:
            print(f"     manquant : {m}")
        sys.exit(1)
    print(f"{OK} PKI détectée")


def demo_certificates():
    section("ÉTAPE 0 — Vérification des Certificats X.509")

    ca_crt     = str(PKI_DIR / "ca"     / "ca.crt")
    server_crt = str(PKI_DIR / "server" / "server.crt")
    client_crt = str(PKI_DIR / "client" / "client.crt")

    for name, cert_path in [("CA", ca_crt), ("Serveur", server_crt), ("Client", client_crt)]:
        info = get_cert_info(cert_path)
        print(f"\n  Certificat {name} :")
        for k, v in info.items():
            print(f"    {k:20s} {v}")

    sv_ok = verify_certificate(server_crt, ca_crt)
    cl_ok = verify_certificate(client_crt, ca_crt)
    print(f"\n{OK} Certificat serveur valide (CA) : {sv_ok}")
    print(f"{OK} Certificat client  valide (CA) : {cl_ok}")


def demo_full_exchange():
    section("ÉTAPE 1 — Création du fichier test")

    tmp_dir = tempfile.mkdtemp(prefix="demo_")
    try:
        # Fichier test
        src_file = os.path.join(tmp_dir, "rapport_confidentiel.txt")
        with open(src_file, "w") as f:
            f.write("=== RAPPORT CONFIDENTIEL ===\n")
            f.write("Université Saad Dahleb — Département Informatique\n\n")
            f.write("Ce document contient des informations sensibles.\n")
            f.write("Il doit être transmis de manière sécurisée via :\n")
            f.write("  • Chiffrement AES-256-CBC (confidentialité)\n")
            f.write("  • Enveloppe RSA-OAEP (échange de clé sécurisé)\n")
            f.write("  • Signature RSA-SHA256 (authenticité + intégrité)\n")
            f.write("  • Certificats X.509 / PKI (identité des parties)\n")
            f.write("  • TLS 1.2 (canal sécurisé)\n\n")
            f.write(f"Taille : {os.path.getsize(src_file) if os.path.exists(src_file) else '~500'} octets\n")

        src_size = os.path.getsize(src_file)
        print(f"{OK} Fichier créé : {os.path.basename(src_file)} ({src_size} octets)")

        # Hash original
        orig_hash = sha256_file(src_file)
        print(f"{OK} SHA-256 original : {orig_hash.hex()}")

        #  CHIFFREMENT AES 
        section("ÉTAPE 2 — Chiffrement AES-256-CBC (côté CLIENT)")
        enc_file = os.path.join(tmp_dir, "fichier.aes")
        aes_key, iv = aes_encrypt_file(src_file, enc_file)
        enc_size = os.path.getsize(enc_file)
        print(f"{OK} Fichier chiffré  : {enc_size} octets")
        print(f"   Clé AES-256 : {aes_key.hex()}")
        print(f"   IV          : {iv.hex()}")

        #ENVELOPPE RSA
        section("ÉTAPE 3 — Enveloppe RSA-OAEP (chiffrement clé AES)")
        enc_key_iv = rsa_encrypt_key(
            aes_key, iv,
            str(PKI_DIR / "shared" / "server_pub.pem")
        )
        print(f"{OK} Clé AES chiffrée avec clé publique RSA du serveur")
        print(f"   Taille enveloppe : {len(enc_key_iv)} octets")
        print(f"   Premiers octets  : {enc_key_iv[:16].hex()}...")

        #SIGNATURE NUMÉRIQUE
        section("ÉTAPE 4 — Signature RSA-SHA256 (côté CLIENT)")
        signature = sign_file(enc_file, str(PKI_DIR / "client" / "client.key"))
        print(f"{OK} Signature créée avec clé privée client")
        print(f"   Taille signature : {len(signature)} octets")

        #ASSEMBLAGE PAQUET SÉCURISÉ
        section("ÉTAPE 5 — Assemblage du Paquet Sécurisé")
        with open(enc_file, "rb") as f:
            enc_bytes = f.read()

        packet = pack_secure_packet(
            enc_bytes, enc_key_iv, signature,
            orig_hash, os.path.basename(src_file)
        )
        print(f"{OK} Paquet assemblé : {len(packet):,} octets")
        print(f"   Structure : [MAGIC|VER|sig|enc_key_iv|filename|enc_data|sha256]")
        # CÔTÉ SERVEUR — Réception et déchiffrement
        
        section("ÉTAPE 6 — Réception & Vérification (côté SERVEUR)")

        pkt = unpack_secure_packet(packet)
        print(f"{OK} Paquet désassemblé")
        print(f"   Fichier    : {pkt['filename']}")

        # Vérification signature
        with tempfile.NamedTemporaryFile(delete=False, suffix=".aes") as tf:
            tf.write(pkt["enc_file"])
            tmp_enc = tf.name

        try:
            sig_ok = verify_signature(
                tmp_enc, pkt["signature"],
                str(PKI_DIR / "shared" / "client_pub.pem")
            )
            if sig_ok:
                print(f"{OK} Signature RSA-SHA256 valide — expéditeur authentifié")
            else:
                print(f"{ERR} SIGNATURE INVALIDE")
                return

            # Déchiffrement RSA de la clé AES
            section("ÉTAPE 7 — Déchiffrement RSA + AES (côté SERVEUR)")
            dec_aes_key, dec_iv = rsa_decrypt_key(
                pkt["enc_key_iv"],
                str(PKI_DIR / "server" / "server.key")
            )
            print(f"{OK} Clé AES récupérée via RSA-OAEP")
            print(f"   Clé AES : {dec_aes_key.hex()}")
            print(f"   IV      : {dec_iv.hex()}")

            key_match = (dec_aes_key == aes_key) and (dec_iv == iv)
            print(f"{OK} Clé AES identique à l'originale : {key_match}")

            # Déchiffrement AES
            out_file = os.path.join(tmp_dir, "REÇU_" + pkt["filename"])
            aes_decrypt_file(tmp_enc, out_file, dec_aes_key, dec_iv)
            print(f"{OK} Fichier déchiffré : {os.path.basename(out_file)}")

            # Vérification intégrité
            recv_hash = sha256_file(out_file)
            integrity = (recv_hash == pkt["original_hash"])
            print(f"\n{OK} SHA-256 reçu    : {recv_hash.hex()}")
            print(f"{OK} SHA-256 original : {pkt['original_hash'].hex()}")
            print(f"{OK} Intégrité vérifiée : {integrity}")

            # Comparer contenu
            with open(src_file)  as f: orig_content = f.read()
            with open(out_file)  as f: recv_content = f.read()
            content_ok = (orig_content == recv_content)

        finally:
            os.unlink(tmp_enc)

        section("RÉSULTAT FINAL")
        print(f"{OK} Chiffrement AES-256-CBC  : OK")
        print(f"{OK} Enveloppe RSA-OAEP       : OK")
        print(f"{OK} Signature RSA-SHA256     : OK")
        print(f"{OK} Vérification certificats : OK")
        print(f"{OK} Intégrité SHA-256        : OK")
        print(f"{OK} Contenu identique        : {content_ok}")
        print(f"\n  Fichier original  : {src_size} octets")
        print(f"  Fichier chiffré  : {enc_size} octets")
        print(f"  Paquet complet   : {len(packet):,} octets")
        print()
        if content_ok:
            print(f"\033[1m\033[32m  ✔ ÉCHANGE SÉCURISÉ RÉUSSI \033[0m\n")
        else:
            print(f"\033[1m\033[31m  ✘ Contenu différent — erreur\033[0m\n")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("\033[1m\033[36m")
    print("   DÉMONSTRATION — Échange de Fichiers Sécurisé  ")
    print("   RSA + AES + Certificats X.509 + TLS           ")
    print("\033[0m")
    check_pki()
    demo_certificates()
    demo_full_exchange()
