# VEX V5 Hub - Community Information Site

A high-performance, mobile-first website aggregating VEX V5 robotics information from around the world.

**Maintained by:** Team 3150N Nighthawks (Ontario, Canada)

## 📱 Project Goal
Build a comprehensive VEX V5 information hub showcasing global competition results, trending robot designs, and community resources. Updated automatically every 4 hours.

## 🚀 Live Website
**URL:** https://d1xek8v0cj8qbn.cloudfront.net

## 📂 Site Sections

### 1. 🏆 Competition
*   **Latest Updates**: News from high-profile VEX V5 competitions globally.
*   **Upcoming Events**: Schedule focusing on major tournaments and the VEX World Championship.
*   **Match Highlights**: Key moments and scores from the community.

### 2. 🤖 Robots
*   **Trending Designs**: Curated collection of viral VEX V5 robot reveals and match videos from social media (TikTok, YouTube, Instagram).
*   **Tech Breakdowns**: Analysis of meta designs and innovative mechanisms.

### 3. 📚 Resources
*   **VEX V5 Program Info**: General information about the VEX V5 platform.
*   **Learning Materials**: Resources for teams and students.
*   **Community Highlights**: Featured content from the global VEX community.

### 4. 🦅 About 3150N
*   **Team Profile**: Information about Team 3150N Nighthawks (site maintainers).
*   **Achievements**: Competition history and awards.
*   **Outreach**: Community engagement and STEM advocacy initiatives.

---

## 🏗️ Architecture

This website is deployed on **AWS** using native services:

- **Hosting:** CloudFront + S3
- **Content Updates:** Lambda + EventBridge (every 4 hours)
- **Domain:** Route 53 (optional)
- **Region:** ca-central-1 (Canada)
- **Profile:** rdp

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

---

## 📦 Project Structure

```
3150N-Nighthawks-Site/
├── dist/                          # Website files
│   ├── index.html                 # Main page (general VEX V5 info)
│   ├── about.html                 # About Team 3150N page
│   ├── css/
│   │   └── styles.css            # Mobile-first CSS
│   └── js/
│       └── app.js                # Dynamic content loader
├── infrastructure/
│   ├── terraform/                # Infrastructure as Code
│   │   ├── providers.tf
│   │   ├── variables.tf
│   │   ├── s3.tf
│   │   ├── cloudfront.tf
│   │   ├── lambda.tf
│   │   ├── eventbridge.tf
│   │   ├── route53.tf
│   │   └── outputs.tf
│   └── lambda/
│       └── content-updater/      # Lambda function
│           └── index.py
├── scripts/
│   └── deploy.sh                 # Deployment helper
├── docs/
│   └── ARCHITECTURE.md           # Architecture documentation
├── DEPLOYMENT.md                 # Deployment guide
└── README.md                     # This file
```

---

## 🛠️ Quick Start

### Prerequisites
- AWS CLI configured with `rdp` profile
- Terraform >= 1.0
- Node.js (for local development)

### Deploy Infrastructure

```bash
# Initialize Terraform
cd infrastructure/terraform
terraform init

# Preview changes
terraform plan

# Deploy to AWS
terraform apply
```

### Deploy Website

```bash
# Sync website files to S3
aws s3 sync ./dist s3://nighthawks-website-899673281585 --delete --profile rdp

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E1QQO6DEN8VF6X --paths '/*' --profile rdp
```

Or use the deployment script:

```bash
./scripts/deploy.sh sync
```

---

## 🔄 Content Updates

Content is automatically updated every 4 hours via Lambda function:
- Global VEX V5 competition results from RobotEvents API
- Upcoming events worldwide
- Trending robot videos from social media
- Technical breakdowns and meta analysis

Manual trigger:
```bash
aws lambda invoke \
  --function-name nighthawks-content-updater \
  --profile rdp \
  --region ca-central-1 \
  /tmp/output.json
```

---

## 💻 Local Development

```bash
# Serve locally (requires a simple HTTP server)
cd dist
python3 -m http.server 8000

# Open in browser
open http://localhost:8000
```

---

## 📝 Configuration

### Custom Domain
1. Edit `infrastructure/terraform/terraform.tfvars`:
   ```hcl
   domain_name = "your-domain.com"
   ```
2. Apply changes:
   ```bash
   terraform apply
   ```

### API Keys
Store API keys in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name nighthawks/vex-api-key \
  --secret-string '{"api_key":"YOUR_KEY"}' \
  --profile rdp
```

---

## 💰 Cost

Estimated monthly cost: **$3-5**
- CloudFront: ~$2
- S3: ~$0.15
- Route 53: ~$1 (if using custom domain)
- Lambda/EventBridge: Free tier

---

## 📚 Documentation

- [Architecture Documentation](docs/ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)

---

## 🔒 Security

- HTTPS enforced via CloudFront
- S3 buckets are private (CloudFront OAC only)
- AES-256 encryption at rest
- IAM least privilege roles

---

## 🤝 Contributing

This is a VEX V5 community information site maintained by Team 3150N Nighthawks.

---

## 📄 License

© 2026 VEX V5 Hub. Maintained by Team 3150N Nighthawks.

---

## 🆘 Support

See [DEPLOYMENT.md](DEPLOYMENT.md) for troubleshooting and management commands.
