#!/bin/bash
# =============================================================================
# Grocerly Deploy Script (ECR + EC2)
# Builds locally, pushes to Amazon ECR, then pulls/restarts on EC2
# =============================================================================

set -euo pipefail

# --------------- CONFIGURATION (edit these) ---------------
AWS_REGION=""                    # e.g. ap-southeast-1
AWS_ACCOUNT_ID=""                # 12-digit AWS account ID
ECR_REPOSITORY="grocerly-web"

EC2_HOST=""                      # e.g. ec2-xx-xx-xx-xx.compute-1.amazonaws.com or IP
EC2_USER="ubuntu"                # ubuntu (Ubuntu AMI) / ec2-user (Amazon Linux)
SSH_KEY=""                       # e.g. ~/.ssh/grocerly-key.pem
REMOTE_DIR="/home/$EC2_USER/grocerly"
SYNC_LOCAL_DB="${SYNC_LOCAL_DB:-0}"  # set to 1 to sync local db.sqlite3 and media/

# ---------- Load local secrets from deploy.sh.local (if exists) ----------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/deploy.sh.local" ]; then
    # shellcheck source=/dev/null
    source "$SCRIPT_DIR/deploy.sh.local"
fi

IMAGE_NAME="grocerly-web"
IMAGE_TAG="$(date +%Y%m%d%H%M%S)-$(git rev-parse --short HEAD 2>/dev/null || echo local)"
# ----------------------------------------------------------

# ---------- Color helpers ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_cmd() {
    command -v "$1" >/dev/null 2>&1 || error "Missing required command: $1"
}

# ---------- Validate config ----------
[ -z "$AWS_REGION" ] && error "Set AWS_REGION in deploy.sh.local (or create from deploy.sh.local.example)"
[ -z "$AWS_ACCOUNT_ID" ] && error "Set AWS_ACCOUNT_ID in deploy.sh.local (or create from deploy.sh.local.example)"
[ -z "$EC2_HOST" ] && error "Set EC2_HOST in deploy.sh.local (or create from deploy.sh.local.example)"
[ -z "$SSH_KEY" ] && error "Set SSH_KEY in deploy.sh.local (or create from deploy.sh.local.example)"
[ ! -f "$SSH_KEY" ] && error "SSH key not found at: $SSH_KEY"

check_cmd aws
check_cmd docker
check_cmd ssh
check_cmd scp

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"
SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST"
SCP_CMD="scp -i $SSH_KEY -o StrictHostKeyChecking=no"

cd "$(dirname "$0")"

# ---------- Step 1: Ensure ECR repository exists ----------
info "Ensuring ECR repository exists..."
if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" >/dev/null 2>&1; then
    aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION" >/dev/null
    info "Created ECR repository: $ECR_REPOSITORY"
fi

# ---------- Step 2: Apply lifecycle policy ----------
if [ -f "ecr-lifecycle-policy.json" ]; then
    info "Applying ECR lifecycle policy..."
    if ! aws ecr put-lifecycle-policy \
        --repository-name "$ECR_REPOSITORY" \
        --lifecycle-policy-text file://ecr-lifecycle-policy.json \
        --region "$AWS_REGION" >/dev/null; then
        warn "Skipping lifecycle policy update (missing ecr:PutLifecyclePolicy permission)."
    fi
fi

# ---------- Step 3: Build image locally ----------
info "Building Docker image locally..."
docker build -t "$IMAGE_NAME:$IMAGE_TAG" .

# ---------- Step 4: Login to ECR and push ----------
info "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

info "Pushing image to ECR..."
docker tag "$IMAGE_NAME:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
docker tag "$IMAGE_NAME:$IMAGE_TAG" "$ECR_URI:latest"
docker push "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:latest"

# ---------- Step 5: Sync deploy files to EC2 ----------
info "Syncing deployment files to EC2..."
$SSH_CMD "mkdir -p $REMOTE_DIR/nginx"
$SCP_CMD docker-compose.yml "$EC2_USER@$EC2_HOST:$REMOTE_DIR/"
$SCP_CMD nginx/default.conf "$EC2_USER@$EC2_HOST:$REMOTE_DIR/nginx/"

if [ -f .env ]; then
    $SCP_CMD .env "$EC2_USER@$EC2_HOST:$REMOTE_DIR/"
else
    warn "No .env found locally; EC2 will use existing .env or defaults"
fi

if [ "$SYNC_LOCAL_DB" = "1" ]; then
    info "SYNC_LOCAL_DB=1 detected: preparing local db/media sync files..."
    [ -f db.sqlite3 ] || error "SYNC_LOCAL_DB=1 but local db.sqlite3 not found"
    $SCP_CMD db.sqlite3 "$EC2_USER@$EC2_HOST:$REMOTE_DIR/db.sqlite3"
    if [ -d media ]; then
        $SCP_CMD -r media "$EC2_USER@$EC2_HOST:$REMOTE_DIR/"
    else
        warn "SYNC_LOCAL_DB=1 but local media/ folder not found; skipping media sync"
    fi
fi

# ---------- Step 6: Pull latest image and restart ----------
info "Deploying on EC2..."
$SSH_CMD << EOF
set -e
cd $REMOTE_DIR

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

WEB_IMAGE=$ECR_URI:$IMAGE_TAG docker compose pull web
WEB_IMAGE=$ECR_URI:$IMAGE_TAG docker compose up -d --remove-orphans

if [ "$SYNC_LOCAL_DB" = "1" ]; then
    echo "Applying local db/media to running containers..."
    docker compose stop web
    docker cp "$REMOTE_DIR/db.sqlite3" grocerly-web:/data/db.sqlite3
    if [ -d "$REMOTE_DIR/media" ]; then
        docker cp "$REMOTE_DIR/media/." grocerly-web:/app/media/
        docker exec grocerly-web sh -lc 'chmod -R a+rX /app/media'
    fi
    docker compose start web
fi

docker image prune -f
docker compose ps
EOF

echo ""
info "=========================================="
info " Deployment successful!"
info " Image: $ECR_URI:$IMAGE_TAG"
info " Site: http://$EC2_HOST"
if [ "$SYNC_LOCAL_DB" = "1" ]; then
    info " Local data sync: enabled (db.sqlite3/media copied)"
fi
info "=========================================="
