#!/bin/bash
# AWS Route 53 Domain Registration Script for vex5hub.com
# This script will register the domain with AWS Route 53

set -e

echo "🌐 AWS Route 53 Domain Registration"
echo "===================================="
echo ""
echo "Domain: vex5hub.com"
echo "Registrar: AWS Route 53"
echo "Cost: ~$13 USD/year"
echo ""

# Check if domain is still available
echo "Checking domain availability..."
AVAILABILITY=$(aws route53domains check-domain-availability \
    --domain-name vex5hub.com \
    --region us-east-1 \
    --profile rdp \
    --query 'Availability' \
    --output text)

if [ "$AVAILABILITY" != "AVAILABLE" ]; then
    echo "❌ Domain is no longer available!"
    exit 1
fi

echo "✅ Domain is available!"
echo ""

# Prompt for contact information
echo "Please provide contact information for domain registration:"
echo "(This will be protected with privacy protection)"
echo ""

read -p "First Name: " FIRST_NAME
read -p "Last Name: " LAST_NAME
read -p "Organization Name [3150N Nighthawks]: " ORG_NAME
ORG_NAME=${ORG_NAME:-"3150N Nighthawks"}

read -p "Email Address: " EMAIL
read -p "Phone Number (format: +1.4165551234): " PHONE

read -p "Address Line 1: " ADDRESS
read -p "City: " CITY
read -p "Province/State (2 letters, e.g., ON): " STATE
read -p "Postal Code (format: M5H 2N2 with space): " ZIPCODE
COUNTRY_CODE="CA"

echo ""
echo "📋 Registration Details:"
echo "  Name: $FIRST_NAME $LAST_NAME"
echo "  Organization: $ORG_NAME"
echo "  Email: $EMAIL"
echo "  Phone: $PHONE"
echo "  Address: $ADDRESS, $CITY, $STATE $ZIPCODE"
echo "  Country: Canada"
echo ""
read -p "Proceed with registration? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Registration cancelled."
    exit 0
fi

echo ""
echo "🚀 Registering domain vex5hub.com..."

# Register the domain
aws route53domains register-domain \
    --domain-name vex5hub.com \
    --duration-in-years 1 \
    --auto-renew \
    --admin-contact \
        FirstName="$FIRST_NAME",LastName="$LAST_NAME",ContactType=COMPANY,OrganizationName="$ORG_NAME",AddressLine1="$ADDRESS",City="$CITY",State="$STATE",CountryCode="$COUNTRY_CODE",ZipCode="$ZIPCODE",PhoneNumber="$PHONE",Email="$EMAIL" \
    --registrant-contact \
        FirstName="$FIRST_NAME",LastName="$LAST_NAME",ContactType=COMPANY,OrganizationName="$ORG_NAME",AddressLine1="$ADDRESS",City="$CITY",State="$STATE",CountryCode="$COUNTRY_CODE",ZipCode="$ZIPCODE",PhoneNumber="$PHONE",Email="$EMAIL" \
    --tech-contact \
        FirstName="$FIRST_NAME",LastName="$LAST_NAME",ContactType=COMPANY,OrganizationName="$ORG_NAME",AddressLine1="$ADDRESS",City="$CITY",State="$STATE",CountryCode="$COUNTRY_CODE",ZipCode="$ZIPCODE",PhoneNumber="$PHONE",Email="$EMAIL" \
    --privacy-protect-admin-contact \
    --privacy-protect-registrant-contact \
    --privacy-protect-tech-contact \
    --region us-east-1 \
    --profile rdp

echo ""
echo "✅ Domain registration initiated!"
echo ""
echo "📧 Next Steps:"
echo "1. Check your email ($EMAIL) for verification"
echo "2. Click the verification link within 15 days"
echo "3. Domain will be active within 24-48 hours"
echo ""
echo "💰 Billing:"
echo "The domain cost (~$13 USD) will be charged to your AWS account."
echo ""
echo "🔧 After Registration:"
echo "Run: cd infrastructure/terraform && terraform apply"
echo "This will automatically configure Route 53 hosted zone and SSL certificate."
