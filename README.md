# Hardlink Manager

Interface web pour créer et gérer des hardlinks (liens physiques) entre fichiers sur le système de fichiers.

## Fonctionnalités

- Interface web intuitive avec explorateur de fichiers
- Création de hardlinks en quelques clics
- Page de réglages pour configurer les répertoires accessibles
- Support multi-architecture (amd64, arm64)

## Installation

### Via Docker Hub

```bash
docker pull loteran/hardlink-manager:latest
```

### Via Docker Compose

```yaml
services:
  hardlink-manager:
    image: loteran/hardlink-manager:latest
    container_name: hardlink-manager
    ports:
      - "5050:5000"
    volumes:
      - /chemin/vers/vos/fichiers:/mnt/data
    restart: unless-stopped
```

### Build local

```bash
git clone https://github.com/loteran/hardlink-manager.git
cd hardlink-manager
docker compose build
docker compose up -d
```

## Configuration

### Volumes

Montez les volumes nécessaires pour que l'application ait accès aux chemins source et destination :

```yaml
volumes:
  - /mnt/Stockage:/mnt/Stockage
  - /mnt/Stockage2:/mnt/Stockage2
```

### Réglages

Accédez à la page des réglages via le bouton "Réglages" pour :
- Ajouter/supprimer des répertoires accessibles dans l'explorateur
- Définir le répertoire de destination par défaut

## Utilisation

1. Accédez à l'interface web (ex: `http://localhost:5050`)
2. Sélectionnez le fichier source dans l'explorateur de gauche
3. Naviguez vers le répertoire de destination
4. Cliquez sur "Créer le Hard Link"

## Architectures supportées

- `linux/amd64`
- `linux/arm64`

## Licence

MIT
