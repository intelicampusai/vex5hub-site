#!/bin/bash

# VEX V5 Hub - Manual Deployment Script
# 
# This script uses the 'rdp' AWS profile to deploy the statically exported Next.js site
# to the appropriate S3 bucket and invalidate the CloudFront cache.

set -e

echo "🚀 Starting deployment process for VEX V5 Hub..."

# 1. Build the Next.js static export
echo "📦 Building the site..."
npm run build

# Ensure the out/ directory was created (Next 14+ uses out/ by default for output: 'export')
if [ ! -d "out" ]; then
  echo "❌ Error: The 'out' directory does not exist. Did the build fail?"
  exit 1
fi

# 2. Deploy to S3
echo "☁️  Syncing files to S3 bucket..."
aws s3 sync ./out s3://vex5hub-website-899673281585 --delete --profile rdp

# 3. Invalidate CloudFront
echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id E2EG8BIAMHW2FN --paths '/*' --profile rdp

echo "✅ Deployment complete! Changes should be live at https://vex5hub.com"
