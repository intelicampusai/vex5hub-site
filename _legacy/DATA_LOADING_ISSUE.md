# Data Loading Issue - Diagnosis & Solution

**Date:** 2026-02-09  
**Status:** 🔧 **IDENTIFIED - FIX IN PROGRESS**

---

## 🔍 Problem

The website at https://d1xek8v0cj8qbn.cloudfront.net is not displaying dynamic content (competitions, robots, events). The JavaScript is trying to fetch JSON data files, but receiving HTML instead.

### Symptoms
- Competition section shows empty cards
- Robots section shows empty cards  
- Browser console errors: `Failed to fetch competitions.json: Unexpected token '<', "<!DOCTYPE "... is not valid JSON`
- Fetching `/data/competitions.json` returns the HTML of `index.html`

---

## 🕵️ Root Cause Analysis

### What's Happening
1. Browser requests: `https://d1xek8v0cj8qbn.cloudfront.net/data/competitions.json`
2. CloudFront matches `/data/*` path pattern → routes to `S3-Data` origin
3. CloudFront strips `/data/` prefix → requests `competitions.json` from data bucket
4. S3 returns 403 Forbidden (OAC permission issue or file not found)
5. CloudFront's custom error response catches the 403
6. CloudFront returns `/index.html` with HTTP 200 status
7. JavaScript receives HTML instead of JSON → parse error

### Verified Facts
✅ Files exist in S3:
- `s3://nighthawks-data-899673281585/competitions.json` (2,006 bytes)
- `s3://nighthawks-data-899673281585/events.json` (1,732 bytes)
- `s3://nighthawks-data-899673281585/robots.json` (4,069 bytes)
- `s3://nighthawks-data-899673281585/team.json` (1,862 bytes)

✅ Content-Type is correct: `application/json`

✅ Bucket policy allows CloudFront:
```json
{
  "Effect": "Allow",
  "Principal": {"Service": "cloudfront.amazonaws.com"},
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::nighthawks-data-899673281585/*",
  "Condition": {
    "StringEquals": {
      "AWS:SourceArn": "arn:aws:cloudfront::899673281585:distribution/E1QQO6DEN8VF6X"
    }
  }
}
```

✅ CloudFront configuration has `/data/*` behavior routing to S3-Data origin

---

## 🐛 The Bug

**CloudFront Custom Error Responses** (lines 94-105 in `cloudfront.tf`):

```hcl
custom_error_response {
  error_code         = 403
  response_code      = 200
  response_page_path = "/index.html"
}

custom_error_response {
  error_code         = 404
  response_code      = 200
  response_page_path = "/index.html"
}
```

These error responses are designed for SPA (Single Page Application) routing, where 404s should redirect to index.html for client-side routing. However, they're **also catching legitimate 403/404 errors from the data bucket**, causing JSON requests to return HTML.

---

## ✅ Solutions

### Solution 1: Remove Custom Error Responses (Quick Fix)
**Pros:** Simple, immediate  
**Cons:** Breaks SPA routing for the main site

**Steps:**
1. Comment out or remove the custom_error_response blocks in `cloudfront.tf`
2. Run `terraform apply`
3. Wait for CloudFront deployment (~15 minutes)

### Solution 2: Use Lambda@Edge (Proper Fix)
**Pros:** Selective error handling, best practice  
**Cons:** More complex, requires Lambda function

**Steps:**
1. Create Lambda@Edge function to intercept origin responses
2. Only redirect to index.html for HTML requests, not JSON
3. Attach to CloudFront distribution
4. Deploy

### Solution 3: Move Data to Website Bucket (Simplest)
**Pros:** Works with current configuration  
**Cons:** Mixes static and dynamic content

**Steps:**
1. Keep data files in website bucket at `/data/*` path
2. Remove the separate S3-Data origin
3. Serve everything from one bucket

### Solution 4: Disable Error Responses for /data/* (Recommended)
**Pros:** Targeted fix, maintains SPA routing  
**Cons:** Requires Terraform update

**Implementation:**
Unfortunately, CloudFront doesn't support path-specific error responses. We need to use Solution 3.

---

## 🚀 Recommended Fix: Solution 3

Move data files to the website bucket and remove the data bucket origin.

### Steps:

1. **Files are already in website bucket** ✅
   ```bash
   s3://nighthawks-website-899673281585/data/competitions.json
   s3://nighthawks-website-899673281585/data/events.json
   s3://nighthawks-website-899673281585/data/robots.json
   s3://nighthawks-website-899673281585/data/team.json
   ```

2. **Update Terraform to remove data bucket origin**:
   - Remove `/data/*` ordered_cache_behavior
   - Remove S3-Data origin
   - Let `/data/*` be served by default behavior (website bucket)

3. **Apply changes**:
   ```bash
   cd infrastructure/terraform
   terraform apply
   ```

4. **Invalidate cache**:
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id E1QQO6DEN8VF6X \
     --paths "/*" \
     --profile rdp
   ```

---

## 🔧 Immediate Workaround

While waiting for Terraform changes, we can test by:

1. **Bypass CloudFront** - Access S3 directly (not recommended for production)
2. **Use different path** - Serve from root instead of `/data/`
3. **Wait for proper fix** - Update Terraform configuration

---

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Data files in S3 | ✅ Working | Files exist with correct content |
| S3 bucket policy | ✅ Working | CloudFront has access |
| CloudFront routing | ⚠️ Configured | Routes to wrong origin |
| Custom error responses | ❌ Blocking | Returning HTML for JSON |
| Cache invalidation | ✅ Complete | Multiple invalidations done |
| Website display | ❌ Not working | No data showing |

---

## 🎯 Next Steps

1. Update `cloudfront.tf` to remove S3-Data origin
2. Remove `/data/*` ordered_cache_behavior  
3. Run `terraform apply`
4. Invalidate CloudFront cache
5. Test website
6. Verify data loads correctly

---

**Estimated Time to Fix:** 20-30 minutes (Terraform apply + CloudFront deployment)

**Impact:** Once fixed, all dynamic content will load correctly and the site will be fully functional.
