# Définitions et Variables — Transfert Sécurisé

> Explication de chaque concept cryptographique et chaque variable utilisés dans le projet.

---

## Table des matières

1. [Concepts cryptographiques](#1-concepts-cryptographiques)
2. [Variables — crypto_utils.py](#2-variables--crypto_utilspy)
3. [Variables — client.py](#3-variables--clientpy)
4. [Variables — server.py](#4-variables--serverpy)
5. [Variables — demo.py](#5-variables--demopy)
6. [Résumé des types de données](#6-résumé-des-types-de-données)

---

## 1. Concepts cryptographiques

### AES — *Advanced Encryption Standard*

C'est l'algorithme de **chiffrement symétrique** utilisé pour chiffrer le contenu du fichier.
"Symétrique" signifie que la **même clé** sert à la fois pour chiffrer et déchiffrer.

```
Fichier lisible   ──[clé AES]──►  Fichier illisible (binaire aléatoire)
Fichier illisible ──[clé AES]──►  Fichier lisible
```

On utilise la variante **AES-256** (clé de 256 bits) en mode **CBC**.

---

### CBC — *Cipher Block Chaining*

C'est le **mode de fonctionnement** d'AES. AES découpe le fichier en blocs de 16 octets et les
chiffre un par un. En mode CBC, chaque bloc est **mélangé avec le résultat du bloc précédent**
avant d'être chiffré. Cela empêche deux blocs identiques de produire le même résultat chiffré.

```
Bloc 1 ──► XOR ──► AES ──► Bloc chiffré 1
              ▲                     │
              │ (IV au départ)      │
              └─────────────────────┘
Bloc 2 ──► XOR ──► AES ──► Bloc chiffré 2 ...
```

---

### IV — *Initialization Vector* (Vecteur d'Initialisation)

C'est un **nombre aléatoire de 16 octets** utilisé pour démarrer la chaîne CBC.
Sans IV, deux fichiers identiques donneraient exactement le même résultat chiffré — ce qui
serait une faille. Grâce à l'IV aléatoire, chaque chiffrement est **unique même pour le même fichier**.

- Généré dans `crypto_utils.py` ligne 15
- N'est **pas secret** (il est envoyé avec le paquet), mais doit être **imprévisible**

---

### RSA — *Rivest–Shamir–Adleman*

C'est l'algorithme de **chiffrement asymétrique**. Il utilise **deux clés différentes** :

- La **clé publique** : tout le monde peut la voir, sert à **chiffrer**
- La **clé privée** : seul le serveur la possède, sert à **déchiffrer**

```
Client connaît :  clé publique du serveur ──► chiffre la clé AES
Serveur possède : clé privée              ──► déchiffre la clé AES
```

On utilise des clés de **2048 bits**.

---

### OAEP — *Optimal Asymmetric Encryption Padding*

C'est le **mode de rembourrage** utilisé avec RSA. Le rembourrage (padding) sert à compléter
les données avec des octets aléatoires avant chiffrement RSA, pour éviter les attaques
mathématiques. OAEP est le standard moderne recommandé (plus sûr que l'ancien PKCS#1 v1.5).

---

### SHA-256 — *Secure Hash Algorithm 256 bits*

C'est une **fonction de hachage**. Elle prend un fichier de n'importe quelle taille et produit
toujours une **empreinte unique de 32 octets (256 bits)**.

```
"Bonjour tout le monde"  ──► SHA-256 ──►  a9f3c2...  (32 octets)
"Bonjour tout le mondE"  ──► SHA-256 ──►  7d1e4f...  (complètement différent)
```

C'est **irréversible** (on ne peut pas retrouver le fichier depuis le hash) et **déterministe**
(même entrée = même hash). Utilisé pour vérifier que le fichier n'a pas été modifié pendant
le transfert.

---

### TLS — *Transport Layer Security*

C'est le protocole qui **chiffre la connexion réseau** entre le client et le serveur
(c'est le même protocole que HTTPS dans les navigateurs). Même si quelqu'un intercepte
les paquets réseau, il ne verra que du bruit chiffré.

---

### PKI — *Public Key Infrastructure*

C'est l'**ensemble des certificats et clés** qui permettent d'identifier et faire confiance
au serveur. Elle comprend une CA, un certificat serveur, et les clés associées.

---

### CA — *Certificate Authority* (Autorité de Certification)

C'est une entité de confiance qui **signe les certificats**. Quand le client se connecte,
il vérifie que le certificat du serveur a bien été signé par la CA qu'il connaît.
Ça empêche quelqu'un de se faire passer pour le serveur.

---

### Chiffrement hybride

C'est la **combinaison d'AES et RSA** utilisée dans ce projet. AES est rapide mais nécessite
un échange de clé sécurisé. RSA résout ce problème mais est trop lent pour chiffrer de gros
fichiers. La solution : **AES chiffre le fichier, RSA chiffre la clé AES**.

```
Fichier (gros) ────────► AES-256  ────────► Fichier chiffré
Clé AES (48 o) ────────► RSA-OAEP ────────► Enveloppe (~256 octets)
```

---

## 2. Variables — `crypto_utils.py`

| Variable | Type | Valeur | Rôle |
|----------|------|--------|------|
| `cle` | `bytes` | 32 octets aléatoires | Clé secrète AES-256 générée aléatoirement à chaque appel |
| `iv` | `bytes` | 16 octets aléatoires | Vecteur d'initialisation pour le mode CBC |
| `donnees` | `bytes` | `cle + iv` = 48 octets | Les deux valeurs concaténées pour être chiffrées en RSA |
| `tmp_entree` | `str` | chemin fichier temp | Fichier temporaire pour écrire les données avant OpenSSL |
| `tmp_sortie` | `str` | chemin fichier temp | Fichier temporaire pour lire le résultat d'OpenSSL |
| `resultat` | `bytes` | ~256 octets | Contenu binaire de l'enveloppe RSA-OAEP chiffrée |
| `donnees_chiffrees` | `bytes` | ~256 octets | Enveloppe RSA reçue en entrée du déchiffrement |
| `h` | `sha256 object` | objet hashlib | Accumulateur SHA-256 mis à jour bloc par bloc |
| `bloc` | `bytes` | 8192 octets max | Un morceau du fichier lu pour le hachage |

---

## 3. Variables — `client.py`

| Variable | Type | Valeur | Rôle |
|----------|------|--------|------|
| `HOTE` | `str` | `"localhost"` | Adresse IP/nom du serveur cible |
| `PORT` | `int` | `9443` | Port réseau du serveur |
| `nom_fichier` | `str` | ex : `"mon_fichier.txt"` | Nom du fichier extrait du chemin complet |
| `hash_original` | `bytes` | 32 octets | Empreinte SHA-256 calculée **avant** chiffrement |
| `fichier_chiffre` | `str` | chemin + `".aes"` | Chemin du fichier AES temporaire sur le disque |
| `cle` | `bytes` | 32 octets | Clé AES générée par `chiffrer_fichier_aes` |
| `iv` | `bytes` | 16 octets | IV généré par `chiffrer_fichier_aes` |
| `cle_chiffree` | `bytes` | ~256 octets | Enveloppe RSA-OAEP contenant `cle + iv` |
| `donnees_chiffrees` | `bytes` | taille variable | Contenu binaire du fichier après chiffrement AES |
| `nom_bytes` | `bytes` | encodage UTF-8 | Nom du fichier en octets pour l'assemblage du paquet |
| `paquet` | `bytes` | tout assemblé | Le paquet binaire complet à envoyer au serveur |
| `contexte` | `SSLContext` | objet TLS | Configuration TLS du client (version minimale, CA) |
| `sock` | `socket` | connexion TCP | Socket TCP brut avant enveloppement TLS |
| `tls` | `SSLSocket` | connexion TLS | Socket chiffré TLS utilisé pour l'envoi |
| `reponse` | `str` | `"OK..."` ou `"ERREUR..."` | Message de confirmation reçu du serveur |

---

## 4. Variables — `server.py`

| Variable | Type | Valeur | Rôle |
|----------|------|--------|------|
| `HOTE` | `str` | `"0.0.0.0"` | Écoute sur toutes les interfaces réseau de la machine |
| `PORT` | `int` | `9443` | Port d'écoute du serveur |
| `DOSSIER` | `str` | `"received_files"` | Répertoire où sauvegarder les fichiers reçus |
| `donnees` | `bytes` | tampon d'accumulation | Buffer de `recevoir_donnees()` pour lire exactement N octets |
| `bloc` | `bytes` | 4096 octets max | Morceau lu depuis le socket à chaque itération |
| `taille_totale` | `int` | nombre d'octets | Taille du paquet complet annoncée par le client (lue en 8 octets) |
| `paquet` | `bytes` | taille variable | Paquet binaire complet reçu du client |
| `offset` | `int` | position en octets | Curseur de lecture dans le paquet pour extraire chaque champ |
| `taille_cle` | `int` | ~256 | Nombre d'octets de l'enveloppe RSA (lu depuis le paquet) |
| `cle_chiffree` | `bytes` | ~256 octets | Enveloppe RSA-OAEP extraite du paquet |
| `hash_original` | `bytes` | 32 octets | Hash SHA-256 envoyé par le client, extrait du paquet |
| `taille_nom` | `int` | longueur du nom | Longueur en octets du nom de fichier (lu sur 2 octets) |
| `nom_fichier` | `str` | ex : `"mon_fichier.txt"` | Nom original du fichier décodé depuis le paquet |
| `taille_donnees` | `int` | taille variable | Taille des données AES chiffrées (lu sur 8 octets) |
| `donnees_chiffrees` | `bytes` | taille variable | Données AES extraites du paquet |
| `cle` | `bytes` | 32 octets | Clé AES récupérée après déchiffrement RSA |
| `iv` | `bytes` | 16 octets | IV récupéré après déchiffrement RSA |
| `tmp` | `str` | chemin fichier temp | Fichier temporaire pour stocker les données AES avant déchiffrement |
| `horodatage` | `str` | ex : `"20260513_160234"` | Date et heure de réception au format `YYYYMMDD_HHMMSS` |
| `chemin_sortie` | `str` | chemin complet | Chemin final du fichier sauvegardé dans `received_files/` |
| `hash_recu` | `bytes` | 32 octets | SHA-256 calculé **après** déchiffrement pour comparaison |
| `contexte` | `SSLContext` | objet TLS | Configuration TLS du serveur (certificat + clé privée) |
| `sock_brut` | `socket` | socket TCP | Socket TCP brut avant enveloppement TLS |
| `sock_tls` | `SSLSocket` | socket TLS | Socket chiffré TLS qui accepte les connexions entrantes |
| `connexion` | `SSLSocket` | connexion client | Socket TLS de la connexion entrante du client |
| `adresse` | `tuple` | `(ip, port)` | Adresse IP et port du client connecté |

---

## 5. Variables — `demo.py`

| Variable | Type | Rôle |
|----------|------|------|
| `fichiers` | `list` | Liste des chemins PKI à vérifier avant la démo |
| `manquants` | `list` | Fichiers PKI absents (déclenche une erreur si non vide) |
| `dossier_tmp` | `str` | Dossier temporaire créé pour tous les fichiers de la démo |
| `fichier_original` | `str` | Chemin du fichier texte créé pour le test |
| `hash_original` | `bytes` | SHA-256 du fichier avant chiffrement |
| `fichier_chiffre` | `str` | Chemin du fichier après chiffrement AES |
| `cle` | `bytes` | Clé AES générée côté "client" |
| `iv` | `bytes` | IV généré côté "client" |
| `cle_chiffree` | `bytes` | Enveloppe RSA après chiffrement de la clé |
| `cle_recue` | `bytes` | Clé AES récupérée côté "serveur" après déchiffrement RSA |
| `iv_recu` | `bytes` | IV récupéré côté "serveur" après déchiffrement RSA |
| `fichier_recu` | `str` | Chemin du fichier déchiffré côté "serveur" |
| `hash_recu` | `bytes` | SHA-256 du fichier déchiffré pour comparaison finale |
| `contenu_original` | `str` | Texte lu depuis le fichier original |
| `contenu_recu` | `str` | Texte lu depuis le fichier déchiffré |

---

## 6. Résumé des types de données

```
bytes       (octets bruts)    → cle, iv, hash, paquet, donnees_chiffrees, cle_chiffree
str         (texte)           → HOTE, nom_fichier, horodatage, chemin_sortie, DOSSIER
int         (nombre entier)   → PORT, taille_totale, taille_cle, taille_nom, offset
socket                        → sock, sock_brut, connexion
SSLContext                    → contexte  (configuration TLS)
SSLSocket                     → tls, sock_tls  (connexion TLS active)
sha256 obj                    → h  (accumulateur de hachage)
list                          → fichiers, manquants
```

---

### Tailles clés à retenir

| Donnée | Taille |
|--------|--------|
| Clé AES (`cle`) | 32 octets = 256 bits |
| IV (`iv`) | 16 octets = 128 bits |
| `cle + iv` avant RSA | 48 octets |
| Enveloppe RSA chiffrée | ~256 octets |
| Hash SHA-256 | 32 octets = 256 bits |
| Entête taille paquet | 8 octets (uint64) |
| Entête taille enveloppe | 4 octets (uint32) |
| Entête taille nom fichier | 2 octets (uint16) |

---

*Document de référence — USTHB Faculté Informatique · 2026*
