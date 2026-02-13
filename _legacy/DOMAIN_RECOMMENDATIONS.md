# Domain Name Recommendations for VEX V5 Hub

**Date:** 2026-02-09  
**Purpose:** Custom domain for the repositioned VEX V5 Hub website

---

## 🎯 Recommended Domain Names to Check

### Top Tier - Short & Memorable

| Domain Name | Why It's Good | Check Here |
|-------------|---------------|------------|
| **nighthawks.com** | Simple, memorable, matches team name | [Check Availability](https://www.namecheap.com/domains/registration/results/?domain=nighthawks.com) |
| **vexhub.com** | Perfect for VEX V5 Hub branding | [Check Availability](https://www.namecheap.com/domains/registration/results/?domain=vexhub.com) |
| **vex5hub.com** | Specific to VEX V5 | [Check Availability](https://www.namecheap.com/domains/registration/results/?domain=vex5hub.com) |

### Second Tier - Descriptive

| Domain Name | Why It's Good | Extension |
|-------------|---------------|-----------|
| **nighthawk-robotics.com** | Clear robotics focus | .com |
| **nighthawkrobotics.com** | No hyphen version | .com |
| **vex-nighthawks.com** | Combines VEX + team name | .com |
| **3150n-nighthawks.com** | Includes team number | .com |
| **nighthawks-vex.com** | Alternative order | .com |

### Third Tier - Alternative Extensions

| Domain Name | Extension | Why Consider |
|-------------|-----------|--------------|
| **nighthawks.org** | .org | Great for educational/team sites |
| **vexhub.org** | .org | Non-profit feel |
| **nighthawks.io** | .io | Tech-focused, trendy |
| **vex5.io** | .io | Short, tech-oriented |

### Creative Options

| Domain Name | Description |
|-------------|-------------|
| **nighthawksvex.com** | Combined, no hyphen |
| **team3150n.com** | Team number focus |
| **vexnighthawks.com** | VEX first |
| **nighthawksrobotics.org** | Full descriptive |

---

## 💡 Recommendation Strategy

### Option 1: Team-Focused (Best for About Page)
If you want to emphasize Team 3150N Nighthawks:
- **Primary:** `nighthawks.com` or `nighthawk-robotics.com`
- **Backup:** `nighthawks.org` or `3150n-nighthawks.com`

### Option 2: Hub-Focused (Best for Main Site)
If you want to emphasize the VEX V5 Hub community aspect:
- **Primary:** `vexhub.com` or `vex5hub.com`
- **Backup:** `vexhub.org` or `vex5.io`

### Option 3: Hybrid Approach
Use the current CloudFront URL for the main hub, and get a custom domain for the team:
- **Main Site:** Keep `d1xek8v0cj8qbn.cloudfront.net` (free)
- **Team About:** Redirect `nighthawks.com` → `about.html`

---

## 🔍 How to Check Availability

### Quick Check (Recommended)
1. Visit [Namecheap Domain Search](https://www.namecheap.com/domains/)
2. Type in your desired domain name
3. See instant availability + pricing

### Alternative Registrars
- **Cloudflare Registrar** - At-cost pricing (no markup)
- **Google Domains** - Simple interface
- **Name.com** - Good for bulk checking
- **GoDaddy** - Wide selection

### Bulk Check Tool
Use [Instant Domain Search](https://instantdomainsearch.com) to check multiple variations at once.

---

## 💰 Estimated Costs

| Registrar | .com Price/year | .org Price/year | .io Price/year |
|-----------|-----------------|-----------------|----------------|
| Namecheap | $13-15 | $14-16 | $35-40 |
| Cloudflare | $9.77 | $9.73 | $32.00 |
| Google Domains | $12 | $12 | $60 |

**Note:** First-year prices often have discounts. Renewal prices are typically higher.

---

## 🚀 Quick Setup Guide (Once Domain is Purchased)

### Step 1: Purchase Domain
Choose your preferred registrar and purchase the domain.

### Step 2: Update Terraform Configuration
Edit `infrastructure/terraform/terraform.tfvars`:
```hcl
domain_name = "nighthawks.com"  # or your chosen domain
```

### Step 3: Apply Terraform Changes
```bash
cd infrastructure/terraform
terraform apply
```

This will:
- Create Route 53 hosted zone
- Request ACM SSL certificate
- Update CloudFront distribution
- Configure DNS records

### Step 4: Update Nameservers
After Terraform completes, get the nameservers:
```bash
terraform output route53_nameservers
```

Update these at your domain registrar (usually in DNS settings).

### Step 5: Wait for Propagation
- DNS propagation: 24-48 hours (usually faster)
- SSL certificate validation: 5-30 minutes
- CloudFront deployment: 15-20 minutes

---

## 📋 Domain Selection Checklist

When choosing your domain, consider:

- [ ] **Memorable** - Easy to remember and spell
- [ ] **Short** - Ideally under 20 characters
- [ ] **No Numbers/Hyphens** - Easier to communicate verbally (unless team number is important)
- [ ] **.com Preferred** - Most recognized extension
- [ ] **Brandable** - Fits your team/hub identity
- [ ] **Available on Social Media** - Check Twitter, Instagram handles
- [ ] **Not Trademarked** - Avoid legal issues
- [ ] **Future-Proof** - Will it still make sense in 5 years?

---

## 🎯 My Top 3 Recommendations

Based on the repositioning to VEX V5 Hub with Team 3150N as maintainers:

### 1. **vexhub.com** ⭐⭐⭐⭐⭐
- **Pros:** Perfect for the VEX V5 Hub branding, short, memorable
- **Cons:** May be taken (need to check)
- **Best For:** Main site focus

### 2. **nighthawks.com** ⭐⭐⭐⭐⭐
- **Pros:** Simple, strong brand, team-focused
- **Cons:** Generic word, may be taken
- **Best For:** Team identity

### 3. **nighthawk-robotics.com** ⭐⭐⭐⭐
- **Pros:** Clear purpose, likely available, professional
- **Cons:** Hyphen can be awkward, longer
- **Best For:** Balanced approach

---

## 🔗 Next Steps

1. **Check Availability** - Use Namecheap or Instant Domain Search
2. **Choose Your Domain** - Based on availability and preference
3. **Purchase** - Recommend Cloudflare for best pricing
4. **Let me know** - I'll help configure Terraform and DNS

---

## 📞 Need Help?

Once you've checked availability and chosen a domain, I can:
- Update Terraform configuration
- Configure Route 53 and ACM
- Set up DNS records
- Test SSL certificate
- Verify domain is working

Just let me know which domain you'd like to use!
