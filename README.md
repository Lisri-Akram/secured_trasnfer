# Secured Transfer

Mini projet Python de transfert de fichier securise entre un client et un serveur.

Le projet utilise un canal TLS, chiffre le contenu du fichier avec AES-256-CBC,
protege la cle AES avec RSA-OAEP, puis verifie l'integrite avec SHA-256 apres
dechiffrement cote serveur.

## Fonctionnement reel

1. Le client calcule le hash SHA-256 du fichier original.
2. Le client genere une cle AES 256 bits et un IV, puis chiffre le fichier avec
   AES-256-CBC via OpenSSL.
3. Le client chiffre la cle AES et l'IV avec la cle publique RSA du serveur
   (`pki/server/server_pub.pem`).
4. Le client construit un paquet binaire contenant :
   - la taille de la cle RSA chiffree, puis la cle RSA chiffree ;
   - le hash SHA-256 original ;
   - la taille du nom de fichier, puis le nom de fichier ;
   - la taille des donnees chiffrees, puis les donnees AES.
5. Le client ouvre une connexion TLS vers `localhost:9443` et verifie le
   certificat serveur avec `pki/ca/ca.crt`.
6. Le serveur recoit le paquet, dechiffre la cle AES avec sa cle privee RSA,
   dechiffre le fichier, puis recalcule le hash SHA-256.
7. Si le hash correspond, le fichier est sauvegarde dans `received_files/` avec
   un prefixe horodate.

## Ce que le projet implemente

- TLS 1.2 minimum entre le client et le serveur.
- Verification du certificat serveur par le client.
- Chiffrement hybride :
  - AES-256-CBC pour le fichier ;
  - RSA-OAEP pour proteger la cle AES et l'IV.
- Verification d'integrite SHA-256 apres reception.
- Demo locale du flux crypto sans reseau avec `demo.py`.

## Ce que le projet n'implemente pas

- Pas d'authentification mutuelle TLS (mTLS) : le serveur ne demande pas de
  certificat client.
- Pas de signature numerique RSA-SHA256.
- Pas de commandes `send`, `ping` ou `list` dans `client.py`.
- Pas de chiffrement authentifie de type AES-GCM : l'integrite est verifiee par
  hash SHA-256 apres dechiffrement.

## Structure

- `client.py` : chiffre un fichier, construit le paquet et l'envoie au serveur.
- `server.py` : ecoute sur le port `9443`, recoit, dechiffre, verifie et
  sauvegarde les fichiers.
- `crypto_utils.py` : fonctions cryptographiques basees sur la commande
  `openssl`.
- `demo.py` : demonstration locale du chiffrement/dechiffrement sans socket.
- `setup_pki.sh` : genere une CA locale, le certificat serveur et la cle
  publique du serveur.
- `received_files/` : dossier de sortie des fichiers recus.

## Prerequis

- Python 3.10+.
- OpenSSL installe et disponible dans le `PATH`.
- Bash pour executer `setup_pki.sh` (Git Bash sous Windows convient).

## Demarrage rapide

Depuis la racine du projet :

```bash
bash setup_pki.sh
```

Lancer le serveur dans un premier terminal :

```bash
python server.py
```

Envoyer un fichier depuis un deuxieme terminal :

```bash
python client.py mon_fichier.txt
```

Le serveur sauvegarde le fichier recu sous une forme similaire a :

```text
received_files/20260513_160000_mon_fichier.txt
```

## Demo locale

Pour tester uniquement la logique cryptographique, sans lancer le serveur :

```bash
python demo.py
```

Sous Windows, si la console affiche une erreur d'encodage sur les caracteres
accentues ou le symbole de succes, lancer plutot :

```bash
python -X utf8 demo.py
```

La demo cree un fichier temporaire, le chiffre, chiffre la cle AES avec RSA,
dechiffre le tout, puis compare le hash SHA-256 du fichier original et du
fichier reconstruit.

## Notes

Ce projet est adapte a une demonstration pedagogique. Pour un usage production,
il faudrait notamment ajouter une authentification forte du client, utiliser un
mode de chiffrement authentifie comme AES-GCM ou ChaCha20-Poly1305, valider plus
strictement les paquets recus et eviter les fichiers temporaires non securises.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE`.
