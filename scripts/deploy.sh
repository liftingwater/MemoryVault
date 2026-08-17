#!/usr/bin/env bash
# Deploy the full MemoryVault stack to AWS.
#
# Usage:
#   ./scripts/deploy.sh [STACK_NAME] [AWS_REGION]
#
# Required env vars:
#   ARTIFACTS_BUCKET   — S3 bucket to stage Lambda code/layer zips
#                        (must already exist; create once with make bootstrap)
#
# Optional env vars:
#   STACK_NAME         — CloudFormation stack name (default: memoryvault)
#   AWS_REGION         — AWS region (default: us-east-1)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

STACK_NAME="${STACK_NAME:-memoryvault}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ARTIFACTS_BUCKET="${ARTIFACTS_BUCKET:?ARTIFACTS_BUCKET env var is required}"

LAMBDA_CODE_KEY="lambda/app.zip"
LAMBDA_LAYER_KEY="lambda/layer.zip"

PACKAGED_TEMPLATE="${ROOT_DIR}/packaged-template.yaml"

echo "==> MemoryVault deploy | stack=${STACK_NAME} region=${AWS_REGION}"

# ── 1. Package Lambda Layer (Python dependencies) ──────────────────────────
echo "--- Packaging Lambda layer..."
LAYER_BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$LAYER_BUILD_DIR"' EXIT

# Build layer inside Lambda-compatible Docker container
# This ensures binary packages (psycopg, pydantic-core) are compiled for Amazon Linux
docker run --rm \
  -v "${ROOT_DIR}/backend/requirements.txt:/requirements.txt:ro" \
  -v "${LAYER_BUILD_DIR}:/out" \
  public.ecr.aws/lambda/python:3.13 \
  bash -c "pip install -q -t /out/python -r /requirements.txt && chmod -R 755 /out"

(cd "${LAYER_BUILD_DIR}" && zip -qr "${ROOT_DIR}/layer.zip" python/)

aws s3 cp "${ROOT_DIR}/layer.zip" "s3://${ARTIFACTS_BUCKET}/${LAMBDA_LAYER_KEY}"
rm -f "${ROOT_DIR}/layer.zip"
echo "    Layer uploaded → s3://${ARTIFACTS_BUCKET}/${LAMBDA_LAYER_KEY}"

# ── 2. Package Lambda function (app code only) ─────────────────────────────
echo "--- Packaging Lambda function..."
APP_BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$APP_BUILD_DIR" "$LAYER_BUILD_DIR"' EXIT

cp -r "${ROOT_DIR}/backend/app" "${APP_BUILD_DIR}/app"
(cd "${APP_BUILD_DIR}" && zip -qr "${ROOT_DIR}/app.zip" app/)

aws s3 cp "${ROOT_DIR}/app.zip" "s3://${ARTIFACTS_BUCKET}/${LAMBDA_CODE_KEY}"
rm -f "${ROOT_DIR}/app.zip"
echo "    App code uploaded → s3://${ARTIFACTS_BUCKET}/${LAMBDA_CODE_KEY}"

# ── 3. Deploy CloudFormation stack ─────────────────────────────────────────
echo "--- Deploying CloudFormation stack '${STACK_NAME}'..."
aws cloudformation deploy \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --template-file "${ROOT_DIR}/template.yaml" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ArtifactsBucket="${ARTIFACTS_BUCKET}" \
    LambdaCodeKey="${LAMBDA_CODE_KEY}" \
    LambdaLayerKey="${LAMBDA_LAYER_KEY}" \
  --no-fail-on-empty-changeset
# AllowedOrigins defaults to * on first deploy — tightened in step 4b below.

# ── 4. Fetch stack outputs ──────────────────────────────────────────────────
echo "--- Fetching stack outputs..."
OUTPUTS=$(aws cloudformation describe-stacks \
  --region "${AWS_REGION}" \
  --stack-name "${STACK_NAME}" \
  --query "Stacks[0].Outputs" \
  --output json)

FRONTEND_BUCKET=$(echo "${OUTPUTS}" | python3 -c "
import json, sys
outputs = json.load(sys.stdin)
print(next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'FrontendBucketName'))
")

DISTRIBUTION_URL=$(echo "${OUTPUTS}" | python3 -c "
import json, sys
outputs = json.load(sys.stdin)
print(next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'DistributionUrl'))
")

FUNCTION_NAME="${STACK_NAME}-api"

# ── 4b. Lock down ALLOWED_ORIGINS to the CloudFront URL ─────────────────────
# The template deploys with AllowedOrigins=* to avoid a circular dependency.
# Now that the stack is up and we have the CloudFront URL, update the Lambda
# environment variable directly so the FastAPI CORS middleware is locked down.
echo "--- Updating Lambda ALLOWED_ORIGINS → ${DISTRIBUTION_URL}..."
CURRENT_ENV=$(aws lambda get-function-configuration \
  --region "${AWS_REGION}" \
  --function-name "${FUNCTION_NAME}" \
  --query "Environment.Variables" \
  --output json)

# Write the updated env to a temp file and use file:// to avoid shell-quoting
# issues with embedded JSON double quotes in --environment Variables=<json>.
TMP_ENV=$(mktemp)
echo "${CURRENT_ENV}" | python3 -c "
import json, sys
env = json.load(sys.stdin)
env['ALLOWED_ORIGINS'] = '${DISTRIBUTION_URL}'
print(json.dumps({'Variables': env}))
" > "${TMP_ENV}"

aws lambda update-function-configuration \
  --region "${AWS_REGION}" \
  --function-name "${FUNCTION_NAME}" \
  --environment "file://${TMP_ENV}" \
  --query "LastUpdateStatus" \
  --output text
rm -f "${TMP_ENV}"
echo "    ALLOWED_ORIGINS locked to ${DISTRIBUTION_URL}"

# ── 5. Build and upload SvelteKit frontend ──────────────────────────────────
echo "--- Building SvelteKit frontend..."
cd "${ROOT_DIR}/frontend" && npm run build

echo "--- Uploading frontend to s3://${FRONTEND_BUCKET}..."
aws s3 sync \
  "${ROOT_DIR}/frontend/build" \
  "s3://${FRONTEND_BUCKET}" \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

# index.html must not be cached (SvelteKit entry point)
aws s3 cp \
  "${ROOT_DIR}/frontend/build/index.html" \
  "s3://${FRONTEND_BUCKET}/index.html" \
  --cache-control "no-cache, no-store, must-revalidate"

# ── 6. Done ─────────────────────────────────────────────────────────────────
echo ""
echo "✓ Deploy complete"
echo "  App URL:  ${DISTRIBUTION_URL}"
echo "  Health:   ${DISTRIBUTION_URL}/health"
echo ""
echo "  Next: update the Supabase connection string in Secrets Manager:"
SECRET_ARN=$(echo "${OUTPUTS}" | python3 -c "
import json, sys
outputs = json.load(sys.stdin)
print(next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'SupabaseSecretArn'))
")
echo "  aws secretsmanager put-secret-value --secret-id ${SECRET_ARN} \\"
echo "    --secret-string '{\"connection_string\":\"YOUR_SUPABASE_URL\"}'"
