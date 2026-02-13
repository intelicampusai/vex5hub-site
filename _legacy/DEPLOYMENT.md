# 3150N Nighthawks Website - Deployment Guide

## 🎉 Deployment Complete!

Your AWS infrastructure has been successfully deployed and the website is live!

---

## 📊 Deployment Summary

### Infrastructure Created (27 AWS Resources)

| Service | Resource | Status |
|---------|----------|--------|
| **S3** | `nighthawks-website-899673281585` | ✅ Live |
| **S3** | `nighthawks-assets-899673281585` | ✅ Live |
| **S3** | `nighthawks-data-899673281585` | ✅ Live |
| **CloudFront** | Distribution `E1QQO6DEN8VF6X` | ✅ Live |
| **Lambda** | `nighthawks-content-updater` | ✅ Active |
| **EventBridge** | `nighthawks-content-update` | ✅ Scheduled (every 4 hours) |
| **IAM** | Lambda & Scheduler Roles | ✅ Configured |
| **CloudWatch** | Lambda Logs | ✅ Monitoring |

---

## 🌐 Website Access

### Live URL
```
https://d1xek8v0cj8qbn.cloudfront.net
```

**Note:** This is the CloudFront default domain. To use a custom domain:
1. Register a domain (e.g., `3150n-nighthawks.com`)
2. Update `infrastructure/terraform/terraform.tfvars` with your domain
3. Run `terraform apply` again
4. Update nameservers at your domain registrar

---

## 📁 S3 Buckets

### Website Bucket
- **Name:** `nighthawks-website-899673281585`
- **Purpose:** Static website files (HTML, CSS, JS)
- **Files Deployed:**
  - `index.html` (7.8 KB)
  - `css/styles.css` (16.4 KB)
  - `js/app.js` (9.3 KB)

### Data Bucket
- **Name:** `nighthawks-data-899673281585`
- **Purpose:** Dynamic content (JSON files updated every 4 hours)
- **Files:**
  - `competitions.json` (346 bytes)
  - `events.json` (338 bytes)
  - `team.json` (283 bytes)
  - `robots.json` (455 bytes)

### Assets Bucket
- **Name:** `nighthawks-assets-899673281585`
- **Purpose:** Media files (images, videos)
- **Status:** Ready for uploads

---

## 🔄 Content Update Schedule

The Lambda function `nighthawks-content-updater` runs automatically:

| Time (UTC) | Action |
|------------|--------|
| Every 4 hours | Fetch latest competition data, events, and robot content |
| Automatic | Upload to S3 data bucket |
| Automatic | Invalidate CloudFront cache |

**Next scheduled run:** Check CloudWatch Events

---

## 🛠️ Management Commands

### Deploy Website Updates
```bash
# Sync website files to S3
aws s3 sync ./dist s3://nighthawks-website-899673281585 --delete --profile rdp

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E1QQO6DEN8VF6X --paths '/*' --profile rdp
```

### Or use the deployment script:
```bash
./scripts/deploy.sh sync
```

### Manually Trigger Content Update
```bash
aws lambda invoke \
  --function-name nighthawks-content-updater \
  --profile rdp \
  --region ca-central-1 \
  /tmp/lambda-output.json
```

### View Lambda Logs
```bash
aws logs tail /aws/lambda/nighthawks-content-updater \
  --follow \
  --profile rdp \
  --region ca-central-1
```

### Check Infrastructure Status
```bash
cd infrastructure/terraform
terraform show
```

---

## 📝 Next Steps

### 1. Configure API Keys (Optional)
To enable live data from VEX RobotEvents API and social media:

```bash
# Create secret in AWS Secrets Manager
aws secretsmanager create-secret \
  --name nighthawks/vex-api-key \
  --secret-string '{"api_key":"YOUR_VEX_API_KEY"}' \
  --profile rdp \
  --region ca-central-1
```

Then update `infrastructure/lambda/content-updater/index.py` to use the API.

### 2. Upload Media Assets
```bash
# Upload images/videos to assets bucket
aws s3 cp ./local-assets/ s3://nighthawks-assets-899673281585/assets/ \
  --recursive \
  --profile rdp
```

### 3. Customize Content
Edit the website files in `dist/` and redeploy:
```bash
./scripts/deploy.sh sync
```

### 4. Add Custom Domain
1. Edit `infrastructure/terraform/terraform.tfvars`:
   ```hcl
   domain_name = "3150n-nighthawks.com"
   ```
2. Apply changes:
   ```bash
   cd infrastructure/terraform
   terraform apply
   ```
3. Update nameservers at your domain registrar with the values from:
   ```bash
   terraform output route53_nameservers
   ```

### 5. Monitor Performance
- **CloudWatch Dashboard:** View Lambda execution metrics
- **CloudFront Reports:** Check cache hit rates and traffic
- **S3 Metrics:** Monitor storage and requests

---

## 💰 Cost Estimate

Based on current deployment:

| Service | Monthly Cost |
|---------|--------------|
| Route 53 | ~$1.00 (if using custom domain) |
| CloudFront | ~$2.00 (10GB transfer, 100K requests) |
| S3 Storage | ~$0.15 (5GB) |
| Lambda | ~$0.00 (free tier) |
| EventBridge | ~$0.00 (free tier) |
| **Total** | **~$3-5/month** |

---

## 🔒 Security Features

✅ **HTTPS Only** - CloudFront enforces TLS 1.2+  
✅ **S3 Bucket Encryption** - AES-256 encryption at rest  
✅ **Private Buckets** - No public access, CloudFront OAC only  
✅ **IAM Least Privilege** - Lambda has minimal required permissions  
✅ **Versioning Enabled** - S3 versioning for rollback capability  

---

## 🐛 Troubleshooting

### Website not loading?
1. Check CloudFront distribution status:
   ```bash
   aws cloudfront get-distribution --id E1QQO6DEN8VF6X --profile rdp
   ```
2. Verify files in S3:
   ```bash
   aws s3 ls s3://nighthawks-website-899673281585/ --recursive --profile rdp
   ```

### Content not updating?
1. Check Lambda logs:
   ```bash
   aws logs tail /aws/lambda/nighthawks-content-updater --follow --profile rdp
   ```
2. Manually invoke Lambda to test:
   ```bash
   aws lambda invoke --function-name nighthawks-content-updater --profile rdp /tmp/test.json
   ```

### Cache not clearing?
Create manual invalidation:
```bash
aws cloudfront create-invalidation \
  --distribution-id E1QQO6DEN8VF6X \
  --paths '/*' \
  --profile rdp
```

---

## 📚 Documentation

- **Architecture:** `docs/ARCHITECTURE.md`
- **Terraform Docs:** `infrastructure/terraform/README.md` (create if needed)
- **Lambda Source:** `infrastructure/lambda/content-updater/index.py`

---

## 🔄 Updating Infrastructure

To modify the infrastructure:

1. Edit Terraform files in `infrastructure/terraform/`
2. Preview changes:
   ```bash
   cd infrastructure/terraform
   terraform plan
   ```
3. Apply changes:
   ```bash
   terraform apply
   ```

---

## 🗑️ Cleanup (Destroy Resources)

**⚠️ Warning:** This will delete all resources and data!

```bash
cd infrastructure/terraform
terraform destroy
```

Or use the deployment script:
```bash
./scripts/deploy.sh destroy
```

---

## 📞 Support

For issues or questions:
- Check AWS CloudWatch Logs
- Review Terraform state: `terraform show`
- Verify AWS credentials: `aws sts get-caller-identity --profile rdp`

---

## ✅ Deployment Checklist

- [x] Terraform infrastructure deployed (27 resources)
- [x] Website files uploaded to S3
- [x] Lambda function tested and working
- [x] Initial content data populated
- [x] CloudFront distribution active
- [x] EventBridge scheduler configured (4-hour interval)
- [ ] Custom domain configured (optional)
- [ ] API keys configured for live data (optional)
- [ ] Media assets uploaded (optional)

---

**Deployed on:** 2026-02-09  
**AWS Profile:** rdp  
**Region:** ca-central-1 (Canada)  
**Website URL:** https://d1xek8v0cj8qbn.cloudfront.net
