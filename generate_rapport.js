const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageBreak, Header, Footer, LevelFormat,
  TabStopType, TabStopPosition, NumberOfPages,
  SimpleField
} = require('docx');
const fs = require('fs');

const BLUE = "1F3864";
const LIGHT_BLUE = "2E75B6";
const VERY_LIGHT_BLUE = "D5E8F0";
const LIGHT_GRAY = "F2F2F2";
const GREEN = "375623";
const ORANGE_BG = "FFF2CC";
const ORANGE_BORDER = "D6B656";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text, bold: true, size: 32, color: BLUE, font: "Arial" })]
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 150 },
    children: [new TextRun({ text, bold: true, size: 26, color: LIGHT_BLUE, font: "Arial" })]
  });
}

function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, bold: true, size: 24, color: "444444", font: "Arial" })]
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 100, after: 120 },
    alignment: opts.center ? AlignmentType.CENTER : AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, size: opts.size || 22, font: "Arial", color: opts.color || "000000", bold: opts.bold || false, italics: opts.italic || false })]
  });
}

function paraRuns(runs, opts = {}) {
  return new Paragraph({
    spacing: { before: 100, after: 120 },
    alignment: AlignmentType.JUSTIFIED,
    children: runs.map(r => new TextRun({ ...r, size: r.size || 22, font: "Arial" }))
  });
}

function emptyLine(n = 1) {
  return Array.from({ length: n }, () => new Paragraph({ children: [new TextRun("")] }));
}

function transition(text) {
  return new Paragraph({
    spacing: { before: 160, after: 80 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, size: 22, font: "Arial", italics: true, color: "555555" })]
  });
}

function makeTable(rows, colWidths, headerRow = true) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: rows.map((row, ri) => new TableRow({
      children: row.map((cell, ci) => new TableCell({
        borders,
        width: { size: colWidths[ci], type: WidthType.DXA },
        shading: { fill: (ri === 0 && headerRow) ? VERY_LIGHT_BLUE : (ri % 2 === 0 ? "FFFFFF" : LIGHT_GRAY), type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          children: [new TextRun({ text: cell, size: 20, font: "Arial", bold: ri === 0 && headerRow, color: ri === 0 && headerRow ? BLUE : "000000" })]
        })]
      }))
    }))
  });
}

// ─── COVER PAGE ───────────────────────────────────────────────────────────────
const coverPage = [
  ...emptyLine(4),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: LIGHT_BLUE, space: 1 } },
    children: [new TextRun({ text: "UNIVERSITÉ SAAD DAHLEB — BLIDA 1", size: 28, bold: true, font: "Arial", color: BLUE, allCaps: true })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 300 },
    children: [new TextRun({ text: "Faculté des Sciences — Département Informatique", size: 24, font: "Arial", color: "444444" })]
  }),
  ...emptyLine(2),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text: "RAPPORT TECHNIQUE", size: 36, bold: true, font: "Arial", color: LIGHT_BLUE, allCaps: true })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 200 },
    children: [new TextRun({ text: "Module : Sécurité Informatique — Cryptographie Appliquée", size: 26, font: "Arial", color: "555555", italics: true })]
  }),
  ...emptyLine(1),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 100 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 6, color: LIGHT_BLUE, space: 1 },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: LIGHT_BLUE, space: 1 }
    },
    children: [new TextRun({ text: "Projet : Système de Transfert de Fichiers Sécurisé", size: 30, bold: true, font: "Arial", color: BLUE })]
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 200 },
    children: [new TextRun({ text: "(secured_transfer)", size: 24, font: "Courier New", color: "777777" })]
  }),
  ...emptyLine(3),
  makeTable([
    ["Auteur", "Étudiant — Département Informatique"],
    ["Encadrant", "Prof. [Nom de l'encadrant]"],
    ["Module", "Sécurité Informatique / Cryptographie Appliquée"],
    ["Niveau", "Licence 3 / Master 1 (à préciser)"],
    ["Date de remise", "27 Avril 2026"],
    ["Langage", "Python 3 + OpenSSL CLI"],
    ["Version du document", "1.0"],
  ], [2800, 6560], true),
  ...emptyLine(4),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Année Universitaire 2025 – 2026", size: 22, font: "Arial", color: "666666" })]
  }),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── RÉSUMÉ EXÉCUTIF ──────────────────────────────────────────────────────────
const resumeExecutif = [
  heading1("Résumé Exécutif"),
  para(
    "Le présent rapport décrit la conception et la mise en œuvre d'un système de transfert de fichiers sécurisé, " +
    "dénommé secured_transfer, développé dans le cadre du module de Sécurité Informatique au Département d'Informatique " +
    "de l'Université Saad Dahleb (Blida 1). Ce projet a pour objectif de démontrer, de manière concrète et fonctionnelle, " +
    "l'application des grands principes de la cryptographie moderne au sein d'une architecture client-serveur réelle."
  ),
  para(
    "L'architecture repose sur un chiffrement hybride combinant l'algorithme symétrique AES-256-CBC pour le chiffrement " +
    "des données volumineuses, et le chiffrement asymétrique RSA-OAEP pour l'échange sécurisé des clés de session. " +
    "L'authenticité des parties est garantie par une infrastructure à clés publiques (PKI) hiérarchique, composée d'une " +
    "autorité de certification (CA) racine et de certificats X.509 délivrés individuellement au client et au serveur."
  ),
  para(
    "Le canal de communication est protégé par le protocole TLS 1.2 en mode d'authentification mutuelle (mTLS), " +
    "imposant une vérification croisée des identités des deux parties. L'intégrité des données transmises est assurée " +
    "par hachage SHA-256, tandis que la non-répudiation est garantie par une signature numérique RSA-SHA256 appliquée " +
    "au fichier chiffré. L'ensemble de ces mécanismes est orchestré autour d'un format de paquet binaire propriétaire, " +
    "baptisé STFX (Secure Transfer File eXchange), dont la structure garantit une désérialisation déterministe et robuste."
  ),
  para(
    "Le projet est structuré en cinq modules distincts (crypto_utils.py, client.py, server.py, demo.py, setup_pki.sh), " +
    "sans dépendance externe à des bibliothèques tierces, s'appuyant exclusivement sur la bibliothèque standard Python " +
    "et les outils OpenSSL système. Une analyse de sécurité identifie les forces de cette implémentation ainsi que " +
    "plusieurs pistes d'amélioration pour un déploiement en environnement de production."
  ),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── SECTION 1 ────────────────────────────────────────────────────────────────
const section1 = [
  heading1("1. Présentation Générale du Projet"),
  para(
    "Le projet secured_transfer constitue une implémentation pédagogique et fonctionnelle d'un système complet de " +
    "transfert de fichiers sécurisé entre deux entités réseau. Il met en pratique les principes fondamentaux de la " +
    "cryptographie appliquée en combinant plusieurs mécanismes complémentaires, chacun répondant à une propriété de " +
    "sécurité distincte."
  ),
  para("Le tableau suivant synthétise les propriétés de sécurité visées et les mécanismes cryptographiques associés :"),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Propriété de sécurité", "Mécanisme cryptographique utilisé"],
    ["Confidentialité", "Chiffrement symétrique AES-256-CBC"],
    ["Échange de clé sécurisé", "Enveloppe asymétrique RSA-OAEP"],
    ["Authenticité des parties", "Signature numérique RSA-SHA256"],
    ["Intégrité des données", "Hachage SHA-256"],
    ["Identité des entités", "Certificats X.509 / Infrastructure PKI"],
    ["Sécurité du canal réseau", "TLS 1.2 minimum avec authentification mutuelle (mTLS)"],
  ], [3400, 5960]),
  new Paragraph({ spacing: { before: 150, after: 0 }, children: [] }),
  transition(
    "Ces propriétés, prises dans leur ensemble, forment une chaîne de confiance cohérente qui sera détaillée " +
    "dans les sections suivantes, en commençant par la structure modulaire du projet."
  ),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── SECTION 2 ────────────────────────────────────────────────────────────────
const section2 = [
  heading1("2. Structure du Projet"),
  para(
    "Le projet est organisé de façon modulaire, séparant clairement les responsabilités cryptographiques, " +
    "réseau et d'infrastructure. L'arborescence ci-dessous présente l'organisation des fichiers :"
  ),
  new Paragraph({
    spacing: { before: 100, after: 100 },
    children: [new TextRun({
      text:
        "secured_transfer/\n" +
        "├── demo.py          — Démonstration locale complète (sans réseau)\n" +
        "├── client.py        — Client TLS d'envoi de fichiers\n" +
        "├── server.py        — Serveur TLS de réception et déchiffrement\n" +
        "├── crypto_utils.py  — Bibliothèque cryptographique (AES, RSA, signature, PKI)\n" +
        "├── setup_pki.sh     — Script de génération de l'infrastructure PKI\n" +
        "└── pki/\n" +
        "    ├── ca/          — Autorité de Certification (CA)\n" +
        "    │   ├── ca.crt   — Certificat racine CA (auto-signé)\n" +
        "    │   └── ca.key   — Clé privée CA (RSA 4096 bits)\n" +
        "    ├── server/      — Certificats du serveur\n" +
        "    ├── client/      — Certificats du client\n" +
        "    └── shared/      — Clés publiques partagées",
      size: 18, font: "Courier New", color: "333333"
    })]
  }),
  transition(
    "Chacun de ces modules remplit un rôle précis dans l'architecture globale. La section suivante en décrit " +
    "le fonctionnement interne de manière détaillée."
  ),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── SECTION 3 ────────────────────────────────────────────────────────────────
const section3 = [
  heading1("3. Description des Modules"),
  transition(
    "Cette section présente successivement chacun des cinq modules composant le projet, en commençant par le " +
    "cœur cryptographique du système."
  ),

  heading2("3.1 Module crypto_utils.py — Couche Cryptographique"),
  para(
    "Ce module constitue le noyau fonctionnel du système. L'intégralité des opérations cryptographiques transite " +
    "par cette couche, qui s'appuie sur l'outil en ligne de commande OpenSSL, invoqué via le module subprocess " +
    "de la bibliothèque standard Python. Cette approche garantit une compatibilité maximale avec les implémentations " +
    "de référence OpenSSL, sans nécessiter de dépendances tierces."
  ),
  heading3("3.1.1 Fonctions principales"),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Fonction", "Rôle"],
    ["aes_encrypt_file()", "Chiffrement d'un fichier par AES-256-CBC avec clé et IV aléatoires"],
    ["aes_decrypt_file()", "Déchiffrement d'un fichier AES-256-CBC"],
    ["rsa_encrypt_key()", "Chiffrement du couple (clé AES ∥ IV) par RSA-OAEP (clé publique destinataire)"],
    ["rsa_decrypt_key()", "Déchiffrement de l'enveloppe RSA pour récupérer la clé AES et l'IV"],
    ["sign_file()", "Signature du condensat SHA-256 d'un fichier par la clé privée RSA"],
    ["verify_signature()", "Vérification d'une signature RSA-SHA256 à partir d'une clé publique ou d'un certificat"],
    ["verify_certificate()", "Vérification qu'un certificat X.509 a été émis par la CA de confiance"],
    ["get_cert_info()", "Extraction des métadonnées d'un certificat (sujet, émetteur, dates de validité)"],
    ["pack_secure_packet()", "Assemblage de tous les éléments cryptographiques en un paquet binaire unique (STFX)"],
    ["unpack_secure_packet()", "Désassemblage et validation du paquet binaire reçu"],
    ["sha256_file()", "Calcul du condensat SHA-256 d'un fichier par blocs de 8 Ko"],
  ], [3200, 6160]),
  new Paragraph({ spacing: { before: 150, after: 0 }, children: [] }),

  heading3("3.1.2 Format du paquet binaire STFX"),
  para(
    "Le format STFX (Secure Transfer File eXchange) est le format propriétaire de sérialisation binaire utilisé " +
    "pour encapsuler l'ensemble des éléments du transfert sécurisé. Sa structure est la suivante :"
  ),
  new Paragraph({
    spacing: { before: 100, after: 100 },
    children: [new TextRun({
      text:
        "┌────────────┬──────────┬────────────────────────┬────────────────────────┐\n" +
        "│ MAGIC (4B) │ VER (1B) │ sig_len (4B) + sig     │ key_len (4B) + enc_key │\n" +
        "├────────────┴──────────┴────────────────────────┴────────────────────────┤\n" +
        "│ fname_len (2B) + filename │ file_size (8B) + données AES │ SHA256 (32B) │\n" +
        "└─────────────────────────────────────────────────────────────────────────┘",
      size: 18, font: "Courier New", color: "333333"
    })]
  }),
  para(
    "Le champ MAGIC est fixé à la valeur littérale « STFX », servant d'identifiant de format. La version du " +
    "protocole est encodée sur un octet (valeur 1). L'ensemble des champs numériques est sérialisé en format " +
    "big-endian conformément aux conventions du module struct de Python."
  ),

  heading2("3.2 Module setup_pki.sh — Infrastructure à Clés Publiques"),
  para(
    "Ce script Bash automatise l'intégralité de la génération de l'infrastructure PKI en six étapes séquentielles. " +
    "Il constitue le point d'entrée obligatoire avant toute utilisation du système."
  ),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Étape", "Action réalisée"],
    ["1", "Génération de la clé privée CA (RSA 4096 bits, protégée par mot de passe)"],
    ["2", "Création du certificat racine CA auto-signé (validité : 10 ans)"],
    ["3", "Génération du certificat serveur (RSA 2048 bits, SAN : localhost / 127.0.0.1)"],
    ["4", "Génération du certificat client (RSA 2048 bits, CN : client01)"],
    ["5", "Extraction des clés publiques RSA vers le répertoire pki/shared/"],
    ["6", "Vérification finale des deux certificats feuilles contre l'autorité CA"],
  ], [1200, 8160]),
  new Paragraph({ spacing: { before: 150, after: 100 }, children: [] }),
  para(
    "Les certificats serveur et client ont une durée de validité d'un an, tandis que la CA est valable dix ans. " +
    "Les informations d'identité (Distinguished Name) sont les suivantes : C=DZ, ST=Blida, " +
    "O=Université Saad Dahleb, OU=Département Informatique."
  ),
  transition(
    "Une fois l'infrastructure PKI en place, le client et le serveur peuvent établir des communications sécurisées. " +
    "Le module client est présenté ci-après."
  ),

  heading2("3.3 Module client.py — Client de Transfert"),
  para(
    "Le module client implémente le protocole d'envoi sécurisé de fichiers sur le réseau. Il expose trois " +
    "commandes principales accessibles en ligne de commande."
  ),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Commande", "Description"],
    ["send <fichier>", "Chiffre et transmet un fichier au serveur via TLS"],
    ["list", "Demande au serveur la liste des fichiers déjà reçus"],
    ["ping", "Vérifie la connectivité TLS avec le serveur"],
  ], [2500, 6860]),
  new Paragraph({ spacing: { before: 150, after: 0 }, children: [] }),
  para("Le protocole d'envoi d'un fichier (commande send) suit les étapes suivantes :"),
  ...[
    "1. Chiffrement local du fichier et assemblage du paquet STFX via encrypt_and_pack_file().",
    "2. Établissement d'une connexion TCP et enveloppement TLS par ssl.wrap_socket.",
    "3. Envoi de la commande SEND_FILE, suivi de l'attente de l'accusé de réception READY.",
    "4. Transmission du paquet : [taille sur 8 octets] [paquet sécurisé].",
    "5. Réception de la confirmation serveur au format OK:<filename>:<size>.",
  ].map(t => new Paragraph({
    spacing: { before: 60, after: 60 },
    numbering: { reference: "steps", level: 0 },
    children: [new TextRun({ text: t, size: 22, font: "Arial" })]
  })),
  new Paragraph({ spacing: { before: 100, after: 0 }, children: [] }),
  para(
    "Le contexte TLS client impose un protocole minimum TLS 1.2, présente le certificat client (mTLS), " +
    "vérifie le certificat serveur via la CA, et active la vérification du nom d'hôte (check_hostname = True)."
  ),

  heading2("3.4 Module server.py — Serveur de Réception"),
  para(
    "Le serveur écoute en permanence sur le port 9443 les connexions TLS entrantes provenant de clients authentifiés. " +
    "Il gère trois types de requêtes."
  ),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Commande reçue", "Traitement effectué"],
    ["SEND_FILE", "Réception, vérification et déchiffrement d'un fichier entrant"],
    ["LIST_FILES", "Renvoi de la liste des fichiers reçus et stockés"],
    ["PING", "Réponse PONG pour valider la connectivité TLS"],
  ], [2500, 6860]),
  new Paragraph({ spacing: { before: 150, after: 0 }, children: [] }),
  para(
    "Le traitement d'un paquet entrant (process_packet) suit un pipeline de vérification strict : " +
    "désassemblage du paquet STFX, vérification de la signature RSA-SHA256, déchiffrement RSA-OAEP " +
    "pour récupérer la clé AES et l'IV, déchiffrement AES-256-CBC du contenu, vérification du condensat " +
    "SHA-256, puis sauvegarde du fichier dans received_files/<horodatage>_<nom_fichier>."
  ),
  para(
    "Les suites de chiffrement TLS autorisées sont restreintes aux suites offrant la confidentialité persistante " +
    "(Perfect Forward Secrecy) : ECDHE-RSA-AES256-GCM-SHA384, ECDHE-RSA-AES128-GCM-SHA256, et DHE-RSA-AES256-GCM-SHA384."
  ),

  heading2("3.5 Module demo.py — Validation Locale"),
  para(
    "Ce module constitue un outil de test et de validation de l'ensemble de la chaîne cryptographique, " +
    "sans nécessiter de communication réseau. Il est destiné à vérifier le bon fonctionnement de toutes " +
    "les primitives cryptographiques dans un environnement local maîtrisé."
  ),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Étape", "Côté", "Action simulée"],
    ["0", "—", "Vérification et affichage des certificats X.509"],
    ["1", "Client", "Création du fichier de test et calcul du condensat SHA-256"],
    ["2", "Client", "Chiffrement AES-256-CBC du fichier"],
    ["3", "Client", "Encapsulation RSA-OAEP de la clé AES et de l'IV"],
    ["4", "Client", "Génération de la signature numérique RSA-SHA256"],
    ["5", "—", "Assemblage du paquet binaire STFX"],
    ["6", "Serveur", "Désassemblage et vérification de la signature"],
    ["7", "Serveur", "Déchiffrement RSA puis AES, vérification du condensat SHA-256"],
  ], [1000, 1500, 6860]),
  new Paragraph({ spacing: { before: 100, after: 0 }, children: [] }),
  transition(
    "Les modules étant clairement définis, la section suivante présente le flux de données global " +
    "illustrant les interactions entre client et serveur lors d'un transfert complet."
  ),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── SECTION 4 ────────────────────────────────────────────────────────────────
const section4 = [
  heading1("4. Flux de Données et Protocole de Transfert"),
  para(
    "Le transfert sécurisé d'un fichier entre le client et le serveur s'effectue selon une séquence " +
    "d'opérations rigoureusement ordonnée, garantissant que chaque propriété de sécurité est satisfaite " +
    "avant l'étape suivante. La figure ci-dessous représente ce flux de façon schématique."
  ),
  heading2("4.1 Phase de traitement côté client"),
  ...[
    "Calcul du condensat SHA-256 du fichier original (F) pour référence d'intégrité.",
    "Chiffrement de F par AES-256-CBC avec une clé et un IV générés aléatoirement → F_chiffré.",
    "Chiffrement du couple (clé AES ∥ IV) par RSA-OAEP avec la clé publique du serveur → enveloppe_clé.",
    "Signature numérique de F_chiffré par la clé privée du client (RSA-SHA256) → signature.",
    "Assemblage de tous ces éléments en un paquet binaire STFX structuré.",
  ].map(t => new Paragraph({
    spacing: { before: 60, after: 60 },
    numbering: { reference: "steps2", level: 0 },
    children: [new TextRun({ text: t, size: 22, font: "Arial" })]
  })),
  heading2("4.2 Phase de communication réseau"),
  para(
    "Le client établit une connexion TCP sur le port 9443 et l'encapsule dans un tunnel TLS 1.2 avec " +
    "authentification mutuelle. Le serveur vérifie le certificat client auprès de la CA avant d'accepter " +
    "la connexion. Le paquet STFX est ensuite transmis précédé de sa taille encodée sur 8 octets."
  ),
  heading2("4.3 Phase de traitement côté serveur"),
  ...[
    "Désassemblage du paquet STFX et extraction des composants.",
    "Vérification de la signature RSA-SHA256 à l'aide de la clé publique du client.",
    "Déchiffrement RSA-OAEP de l'enveloppe de clé par la clé privée du serveur → clé AES + IV.",
    "Déchiffrement AES-256-CBC du contenu chiffré → fichier reconstruit F_reçu.",
    "Vérification de l'intégrité : SHA-256(F_reçu) == condensat_original.",
    "Sauvegarde du fichier et envoi de l'accusé de réception OK:<filename>:<taille>.",
  ].map(t => new Paragraph({
    spacing: { before: 60, after: 60 },
    numbering: { reference: "steps3", level: 0 },
    children: [new TextRun({ text: t, size: 22, font: "Arial" })]
  })),
  new Paragraph({ spacing: { before: 100, after: 0 }, children: [] }),
  transition(
    "Ce protocole rigoureux offre de solides garanties de sécurité. La section suivante en dresse " +
    "une analyse critique, identifiant les points forts et les axes d'amélioration."
  ),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── SECTION 5 ────────────────────────────────────────────────────────────────
const section5 = [
  heading1("5. Analyse de Sécurité"),
  para(
    "Cette section propose une évaluation critique des choix cryptographiques et architecturaux retenus " +
    "dans le projet, en identifiant les points forts de l'implémentation ainsi que les vulnérabilités " +
    "ou insuffisances qui devraient être corrigées avant tout déploiement en environnement de production."
  ),

  heading2("5.1 Points forts de l'implémentation"),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Point fort", "Justification technique"],
    ["Chiffrement hybride (AES + RSA)", "Architecture standard et efficace : AES pour le volume de données, RSA pour l'échange de clé de session"],
    ["Padding RSA-OAEP", "Résistance aux attaques de type Bleichenbacher contrairement au padding PKCS#1 v1.5"],
    ["Authentification mutuelle (mTLS)", "Vérification croisée des identités des deux parties par certificat X.509"],
    ["Signature sur fichier chiffré", "Évite les attaques de type « sign-then-encrypt » — la signature porte sur le texte chiffré"],
    ["Vérification d'intégrité SHA-256", "Détection de toute altération des données transmises"],
    ["TLS 1.2 minimum imposé", "Désactivation des versions vulnérables (SSLv3, TLS 1.0, TLS 1.1)"],
    ["Perfect Forward Secrecy (PFS)", "Seules les suites ECDHE et DHE sont autorisées — compromission de la clé longue terme sans impact sur sessions passées"],
    ["PKI hiérarchique", "Séparation claire entre l'autorité de certification et les certificats feuilles"],
  ], [3200, 6160]),

  heading2("5.2 Points à améliorer"),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Problème identifié", "Recommandation"],
    ["Commande openssl rsautl dépréciée", "Remplacer par openssl pkeyutl dans toutes les invocations OpenSSL"],
    ["Clé CA non protégée hors ligne", "Stocker la clé CA sur un HSM ou un support chiffré hors ligne en production"],
    ["Absence de révocation (CRL/OCSP)", "Implémenter une liste de révocation (CRL) ou un service OCSP"],
    ["Serveur mono-thread", "Intégrer threading.Thread ou asyncio pour la gestion de connexions simultanées"],
    ["Fichiers temporaires non chiffrés", "Supprimer systématiquement les fichiers .bin et .enc temporaires via un bloc finally"],
    ["TLS 1.3 non imposé", "Recommander TLS 1.3 comme version minimale pour tout nouveau déploiement"],
    ["Mot de passe CA codé en dur", "Externaliser la gestion du secret de la CA vers un gestionnaire de secrets sécurisé"],
  ], [3200, 6160]),
  new Paragraph({ spacing: { before: 100, after: 0 }, children: [] }),
  transition(
    "Ces observations permettent de positionner le projet comme une base solide pour un développement " +
    "académique, tout en identifiant clairement les prérequis à satisfaire pour une mise en production."
  ),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── SECTION 6 ────────────────────────────────────────────────────────────────
const section6 = [
  heading1("6. Dépendances et Prérequis"),
  para(
    "Le projet ne nécessite aucune installation de bibliothèque tierce via pip ou tout autre gestionnaire " +
    "de paquets. Il repose exclusivement sur la bibliothèque standard Python et l'outil OpenSSL fourni " +
    "par le système d'exploitation."
  ),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Dépendance", "Version minimale", "Rôle"],
    ["Python", "3.9+", "Langage principal (support des annotations de types tuple[bytes, bytes])"],
    ["OpenSSL (CLI)", "Système", "Toutes les primitives cryptographiques (AES, RSA, condensats)"],
    ["ssl", "stdlib", "Gestion du contexte et du handshake TLS"],
    ["socket", "stdlib", "Communication réseau TCP bas niveau"],
    ["struct", "stdlib", "Sérialisation binaire du paquet STFX (big-endian)"],
    ["hashlib", "stdlib", "Calcul du condensat SHA-256"],
    ["subprocess", "stdlib", "Invocation des commandes OpenSSL en ligne de commande"],
    ["tempfile", "stdlib", "Création et gestion de fichiers temporaires sécurisés"],
  ], [2200, 1500, 5660]),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── SECTION 7 ────────────────────────────────────────────────────────────────
const section7 = [
  heading1("7. Guide d'Utilisation"),
  para(
    "Cette section décrit les étapes nécessaires pour déployer et utiliser le système de transfert " +
    "sécurisé dans un environnement local de développement."
  ),

  heading2("7.1 Étape 1 — Initialisation de l'infrastructure PKI"),
  new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text: "bash setup_pki.sh", size: 20, font: "Courier New", color: "1F3864" })]
  }),
  para(
    "Cette commande génère l'ensemble des clés et certificats nécessaires au fonctionnement du système. " +
    "Elle doit être exécutée une seule fois avant tout démarrage du serveur ou du client."
  ),

  heading2("7.2 Étape 2 — Validation locale de la chaîne cryptographique"),
  new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text: "python demo.py", size: 20, font: "Courier New", color: "1F3864" })]
  }),
  para(
    "Ce script exécute un test de bout en bout de l'intégralité de la chaîne cryptographique en environnement " +
    "local, sans communication réseau. Il est recommandé de l'exécuter après chaque modification du code."
  ),

  heading2("7.3 Étape 3 — Démarrage du serveur réseau"),
  new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text: "python server.py", size: 20, font: "Courier New", color: "1F3864" })]
  }),
  para(
    "Le serveur écoute sur toutes les interfaces réseau disponibles (0.0.0.0) sur le port 9443."
  ),

  heading2("7.4 Étape 4 — Utilisation du client"),
  new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({
      text: "python client.py send mon_fichier.txt\npython client.py list\npython client.py ping",
      size: 20, font: "Courier New", color: "1F3864"
    })]
  }),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── SECTION 8 — CONCLUSION ───────────────────────────────────────────────────
const section8 = [
  heading1("8. Conclusion et Perspectives"),
  heading2("8.1 Bilan du projet"),
  para(
    "Le projet secured_transfer atteint ses objectifs pédagogiques en proposant une implémentation " +
    "fonctionnelle et cohérente d'un système de transfert de fichiers sécurisé. Il illustre concrètement " +
    "l'articulation entre les grands mécanismes de la cryptographie moderne : chiffrement hybride, " +
    "infrastructure à clés publiques, signature numérique et protocole sécurisé à authentification mutuelle."
  ),
  para(
    "L'architecture adoptée respecte les bonnes pratiques de l'industrie en matière de séparation des " +
    "responsabilités, d'utilisation d'algorithmes éprouvés et de vérification systématique de chaque " +
    "propriété de sécurité (confidentialité, authenticité, intégrité, non-répudiation). L'absence de " +
    "dépendances tierces renforce la lisibilité du code et facilite la compréhension des mécanismes sous-jacents."
  ),
  para(
    "Sur le plan des limites, l'analyse de la section 5.2 a mis en évidence plusieurs points d'attention " +
    "importants : utilisation de commandes OpenSSL dépréciées, absence de mécanisme de révocation de " +
    "certificats, gestion insuffisante des fichiers temporaires, et absence de support multi-client au " +
    "niveau du serveur. Ces points, bien que non bloquants dans un contexte académique, doivent impérativement " +
    "être adressés avant tout déploiement en environnement de production."
  ),

  heading2("8.2 Perspectives d'évolution"),
  para(
    "Plusieurs axes d'amélioration peuvent être envisagés pour enrichir ce projet et le rapprocher d'une " +
    "solution prête pour la production :"
  ),
  ...[
    "Migration vers TLS 1.3 comme version de protocole minimale imposée.",
    "Mise en place d'un service OCSP (Online Certificate Status Protocol) pour la révocation en temps réel.",
    "Remplacement des appels subprocess OpenSSL par la bibliothèque Python cryptography (pyca/cryptography) pour une meilleure portabilité.",
    "Implémentation d'un serveur multi-thread ou asynchrone (asyncio) pour la gestion de connexions simultanées.",
    "Chiffrement des fichiers temporaires et suppression sécurisée garantie par des blocs finally.",
    "Intégration d'un système de journalisation d'audit (audit trail) pour la traçabilité des transferts.",
    "Extension du protocole pour supporter la reprise sur erreur et le transfert de fichiers volumineux par fragments (chunking).",
  ].map(t => new Paragraph({
    spacing: { before: 60, after: 60 },
    numbering: { reference: "prospects", level: 0 },
    children: [new TextRun({ text: t, size: 22, font: "Arial" })]
  })),
  new Paragraph({ spacing: { before: 150, after: 0 }, children: [] }),
  para(
    "En définitive, ce projet constitue une base solide et extensible pour l'étude et l'enseignement " +
    "de la cryptographie appliquée, offrant un terrain d'expérimentation concret sur des problématiques " +
    "directement transposables dans l'industrie."
  ),
  new Paragraph({ children: [new PageBreak()] })
];

// ─── GLOSSAIRE ────────────────────────────────────────────────────────────────
const glossaire = [
  heading1("Glossaire des Termes Techniques"),
  para(
    "Ce glossaire définit les termes cryptographiques et techniques utilisés tout au long de ce rapport, " +
    "dans l'ordre alphabétique."
  ),
  new Paragraph({ spacing: { before: 100, after: 100 }, children: [] }),
  makeTable([
    ["Terme / Acronyme", "Définition"],
    ["AES (Advanced Encryption Standard)", "Algorithme de chiffrement symétrique par blocs, standardisé par le NIST en 2001. En mode AES-256-CBC, il utilise une clé de 256 bits et le mode CBC (Cipher Block Chaining) qui enchaîne les blocs pour renforcer la sécurité."],
    ["CA (Certificate Authority)", "Autorité de Certification : entité de confiance chargée de signer numériquement les certificats X.509, garantissant ainsi l'identité de leur titulaire."],
    ["CBC (Cipher Block Chaining)", "Mode d'opération pour les chiffrements par blocs dans lequel chaque bloc de texte chiffré est combiné (XOR) avec le bloc précédent avant chiffrement, rendant chaque bloc dépendant de tous les précédents."],
    ["CRL (Certificate Revocation List)", "Liste de révocation de certificats : fichier signé par la CA listant les certificats révoqués avant leur date d'expiration."],
    ["ECDHE (Elliptic Curve Diffie-Hellman Ephemeral)", "Variante à courbe elliptique de l'échange Diffie-Hellman utilisant des clés éphémères, garantissant la confidentialité persistante (PFS)."],
    ["HSM (Hardware Security Module)", "Module matériel de sécurité conçu pour stocker et manipuler des clés cryptographiques dans un environnement physiquement protégé contre l'extraction."],
    ["IV (Initialization Vector)", "Vecteur d'initialisation : valeur aléatoire non secrète utilisée en mode CBC pour diversifier le chiffrement même lorsque deux messages identiques sont chiffrés avec la même clé."],
    ["mTLS (Mutual TLS)", "Variante de TLS dans laquelle les deux parties (client et serveur) s'authentifient mutuellement par certificat X.509, contrairement au TLS standard où seul le serveur est authentifié."],
    ["OAEP (Optimal Asymmetric Encryption Padding)", "Schéma de padding probabiliste pour le chiffrement RSA, défini dans PKCS#1 v2.x. Résistant aux attaques adaptatives à texte chiffré choisi (IND-CCA2), contrairement au padding PKCS#1 v1.5."],
    ["OCSP (Online Certificate Status Protocol)", "Protocole permettant de vérifier en temps réel la validité d'un certificat X.509 auprès de l'autorité de certification, en alternative aux CRL."],
    ["PFS (Perfect Forward Secrecy)", "Propriété d'un protocole garantissant que la compromission d'une clé à long terme ne permet pas de déchiffrer rétroactivement les sessions passées. Obtenue par l'utilisation de clés de session éphémères (Diffie-Hellman)."],
    ["PKI (Public Key Infrastructure)", "Infrastructure à clés publiques : ensemble de politiques, de procédures et de systèmes permettant la création, la gestion, la distribution et la révocation de certificats numériques."],
    ["RSA (Rivest–Shamir–Adleman)", "Algorithme de chiffrement asymétrique à clé publique, dont la sécurité repose sur la difficulté de la factorisation de grands entiers. Utilisé ici pour le chiffrement de clé (OAEP) et la signature numérique (SHA256)."],
    ["SAN (Subject Alternative Name)", "Extension d'un certificat X.509 permettant d'associer plusieurs identifiants (noms de domaine, adresses IP) à un même certificat."],
    ["SHA-256 (Secure Hash Algorithm 256)", "Fonction de hachage cryptographique de la famille SHA-2 produisant un condensat de 256 bits. Utilisée ici pour la vérification d'intégrité et comme base de la signature numérique."],
    ["STFX (Secure Transfer File eXchange)", "Format binaire propriétaire défini dans ce projet pour encapsuler l'ensemble des éléments d'un transfert sécurisé (données chiffrées, enveloppe de clé, signature, condensat) en un paquet unique."],
    ["TLS (Transport Layer Security)", "Protocole cryptographique de sécurisation des communications réseau, successeur de SSL. TLS 1.2 et 1.3 sont les versions actuellement recommandées."],
    ["X.509", "Standard de format de certificat à clé publique défini par l'ITU-T, utilisé notamment dans les infrastructures PKI, TLS et les signatures numériques."],
  ], [2800, 6560]),
];

// ─── ASSEMBLE DOCUMENT ────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "steps",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "steps2",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "steps3",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "prospects",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
    ]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: LIGHT_BLUE },
        paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "444444" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            spacing: { before: 0, after: 120 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: LIGHT_BLUE, space: 1 } },
            children: [
              new TextRun({ text: "Rapport Technique — Projet secured_transfer", size: 18, font: "Arial", color: "777777", italics: true }),
              new TextRun({ text: "\t", size: 18 }),
              new TextRun({ text: "Université Saad Dahleb — 2025/2026", size: 18, font: "Arial", color: "777777", italics: true }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }]
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            spacing: { before: 80, after: 0 },
            border: { top: { style: BorderStyle.SINGLE, size: 6, color: LIGHT_BLUE, space: 1 } },
            children: [
              new TextRun({ text: "Département Informatique", size: 16, font: "Arial", color: "999999" }),
              new TextRun({ text: "\t", size: 16 }),
              new TextRun({ text: "Page ", size: 16, font: "Arial", color: "999999" }),
              new SimpleField({ instrText: "PAGE", cachedValue: "1" }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }]
          })
        ]
      })
    },
    children: [
      ...coverPage,
      ...resumeExecutif,
      ...section1,
      ...section2,
      ...section3,
      ...section4,
      ...section5,
      ...section6,
      ...section7,
      ...section8,
      ...glossaire,
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("c:\\secured_trasnfer\\Rapport_Secured_Transfer_Final.docx", buf);
  console.log("Done.");
});
