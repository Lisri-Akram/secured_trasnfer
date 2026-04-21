# Secured Transfer

Mini projet Python pour envoyer des fichiers de maniere securisee entre un client et un serveur.

## Fonctions

- Canal TLS 1.2+
- Authentification mutuelle par certificats (mTLS)
- Chiffrement du fichier en AES-256-CBC
- Chiffrement de la cle AES avec RSA-OAEP
- Signature numerique RSA-SHA256
- Verification d'integrite SHA-256

## Structure

- `server.py` : serveur TLS qui recoit, verifie et dechiffre les fichiers
- `client.py` : client TLS qui chiffre, signe et envoie un fichier
- `crypto_utils.py` : fonctions crypto (OpenSSL)
- `demo.py` : demo locale du flux complet (sans reseau)
- `setup_pki.sh` : generation des certificats/cles (PKI)

## Prerequis

- Python 3.10+
- OpenSSL installe et accessible dans le PATH
- Bash (Git Bash sur Windows)

## Demarrage rapide

1. Generer la PKI :

```bash
bash setup_pki.sh
```

2. Lancer le serveur :

```bash
python server.py
```

3. Dans un autre terminal, envoyer un fichier :

```bash
python client.py send mon_fichier.txt
```

## Commandes utiles

```bash
python client.py ping
python client.py list
python demo.py
```

Les fichiers recus sont enregistres dans le dossier `received_files/`.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE`.


