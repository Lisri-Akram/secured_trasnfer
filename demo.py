"""
demo.py
Démonstration complète en local (sans réseau).
Simule l'envoi et la réception d'un fichier chiffré.

Utilisation : python demo.py
"""

import os
import sys
import tempfile
import shutil

from crypto_utils import (
    chiffrer_fichier_aes, dechiffrer_fichier_aes,
    chiffrer_cle_rsa,    dechiffrer_cle_rsa,
    hash_sha256
)


def verifier_pki():
    """Vérifie que les fichiers PKI nécessaires existent."""
    fichiers = [
        "pki/ca/ca.crt",
        "pki/server/server.crt",
        "pki/server/server.key",
        "pki/server/server_pub.pem",
    ]
    manquants = [f for f in fichiers if not os.path.exists(f)]
    if manquants:
        print("PKI manquante ! Exécutez d'abord : bash setup_pki.sh")
        for f in manquants:
            print(f"  manquant : {f}")
        sys.exit(1)
    print("✔ PKI détectée\n")


def main():
    print("=" * 50)
    print("  DEMO — Échange de Fichiers Sécurisé")
    print("  AES-256 + RSA-OAEP + Certificat X.509")
    print("=" * 50)

    verifier_pki()

    # Créer un dossier temporaire
    dossier_tmp = tempfile.mkdtemp()

    try:
        # ─────────────────────────────────────────────
        # ÉTAPE 1 : Créer le fichier à envoyer
        # ─────────────────────────────────────────────
        print("ETAPE 1 : Création du fichier")
        fichier_original = os.path.join(dossier_tmp, "message.txt")
        with open(fichier_original, "w") as f:
            f.write("Bonjour !\n")
            f.write("Ceci est un fichier confidentiel.\n")
            f.write("Université Saad Dahleb — Informatique\n")

        print(f"  Fichier : {os.path.basename(fichier_original)}")
        print(f"  Taille  : {os.path.getsize(fichier_original)} octets")

        # ─────────────────────────────────────────────
        # ÉTAPE 2 : Calculer le hash SHA-256
        # ─────────────────────────────────────────────
        print("\nETAPE 2 : Hash SHA-256 du fichier original")
        hash_original = hash_sha256(fichier_original)
        print(f"  Hash : {hash_original.hex()}")

        # ─────────────────────────────────────────────
        # ÉTAPE 3 : Chiffrer le fichier avec AES-256
        # ─────────────────────────────────────────────
        print("\nETAPE 3 : Chiffrement AES-256-CBC (côté client)")
        fichier_chiffre = os.path.join(dossier_tmp, "message.aes")
        cle, iv = chiffrer_fichier_aes(fichier_original, fichier_chiffre)
        print(f"  Clé AES : {cle.hex()}")
        print(f"  IV      : {iv.hex()}")
        print(f"  Taille fichier chiffré : {os.path.getsize(fichier_chiffre)} octets")

        # ─────────────────────────────────────────────
        # ÉTAPE 4 : Chiffrer la clé AES avec RSA
        # ─────────────────────────────────────────────
        print("\nETAPE 4 : Chiffrement RSA-OAEP de la clé AES (côté client)")
        cle_chiffree = chiffrer_cle_rsa(cle, iv, "pki/server/server_pub.pem")
        print(f"  Clé chiffrée : {len(cle_chiffree)} octets")

        # ─────────────────────────────────────────────
        # ÉTAPE 5 : Déchiffrer la clé AES avec RSA
        # ─────────────────────────────────────────────
        print("\nETAPE 5 : Déchiffrement RSA-OAEP (côté serveur)")
        cle_recue, iv_recu = dechiffrer_cle_rsa(cle_chiffree, "pki/server/server.key")
        print(f"  Clé récupérée : {cle_recue.hex()}")
        print(f"  Clés identiques : {cle == cle_recue}")

        # ─────────────────────────────────────────────
        # ÉTAPE 6 : Déchiffrer le fichier avec AES
        # ─────────────────────────────────────────────
        print("\nETAPE 6 : Déchiffrement AES-256-CBC (côté serveur)")
        fichier_recu = os.path.join(dossier_tmp, "message_recu.txt")
        dechiffrer_fichier_aes(fichier_chiffre, fichier_recu, cle_recue, iv_recu)
        print(f"  Fichier déchiffré : {os.path.basename(fichier_recu)}")

        # ─────────────────────────────────────────────
        # ÉTAPE 7 : Vérifier l'intégrité SHA-256
        # ─────────────────────────────────────────────
        print("\nETAPE 7 : Vérification SHA-256")
        hash_recu = hash_sha256(fichier_recu)
        print(f"  Hash original : {hash_original.hex()}")
        print(f"  Hash reçu     : {hash_recu.hex()}")
        print(f"  Intégrité OK  : {hash_original == hash_recu}")

        # ─────────────────────────────────────────────
        # Résultat final
        # ─────────────────────────────────────────────
        print("\n" + "=" * 50)
        with open(fichier_original) as f: contenu_original = f.read()
        with open(fichier_recu)    as f: contenu_recu     = f.read()

        if contenu_original == contenu_recu:
            print("  ✔ SUCCÈS — Fichier transmis correctement !")
        else:
            print("  ✘ ERREUR — Contenu différent !")
        print("=" * 50 + "\n")

    finally:
        shutil.rmtree(dossier_tmp)


if __name__ == "__main__":
    main()
