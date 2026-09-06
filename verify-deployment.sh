#!/bin/bash
# LogiRush Deployment Verification Script
# Run this after deployment to verify everything is connected correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   LogiRush Deployment Verification        ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo ""

# Function to check URL
check_url() {
    local url=$1
    local name=$2
    local expected=$3
    
    echo -ne "Checking ${name}... "
    
    if response=$(curl -s -f -m 10 "$url" 2>/dev/null); then
        if [[ -n "$expected" ]] && [[ "$response" == *"$expected"* ]]; then
            echo -e "${GREEN}✓ OK${NC}"
            return 0
        elif [[ -z "$expected" ]]; then
            echo -e "${GREEN}✓ OK${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Unexpected response${NC}"
            echo "Response: $response"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Get URLs from user
echo -e "${YELLOW}Enter your deployment URLs:${NC}"
echo ""

read -p "Backend URL (e.g., https://your-backend.onrender.com): " BACKEND_URL
BACKEND_URL=${BACKEND_URL%/}  # Remove trailing slash

read -p "Frontend URL (e.g., https://your-app.vercel.app): " FRONTEND_URL
FRONTEND_URL=${FRONTEND_URL%/}

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}Testing Backend${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Test backend health
check_url "$BACKEND_URL/health" "Health endpoint" '"status":"ok"'

# Test weather endpoint
check_url "$BACKEND_URL/api/ner/weather" "Weather data" '"data"'

# Test auth endpoint
check_url "$BACKEND_URL/api/auth/demo-check" "Auth system" || echo "  (This is OK if endpoint doesn't exist)"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}Testing Frontend${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Test frontend
check_url "$FRONTEND_URL" "Frontend homepage"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}Configuration Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Check frontend env file
if [ -f "routeOptimiserFrontend/.env" ]; then
    FRONTEND_API_URL=$(grep VITE_API_BASE_URL routeOptimiserFrontend/.env | cut -d '=' -f2)
    if [ "$FRONTEND_API_URL" == "$BACKEND_URL" ]; then
        echo -e "Frontend .env: ${GREEN}✓ Matches backend URL${NC}"
    else
        echo -e "Frontend .env: ${YELLOW}⚠ Mismatch!${NC}"
        echo "  Expected: $BACKEND_URL"
        echo "  Found: $FRONTEND_API_URL"
    fi
else
    echo -e "Frontend .env: ${YELLOW}⚠ File not found (OK if deployed)${NC}"
fi

# Check mobile app env file
if [ -f "nerFieldApp/.env" ]; then
    MOBILE_API_URL=$(grep EXPO_PUBLIC_API_BASE_URL nerFieldApp/.env | cut -d '=' -f2)
    if [ "$MOBILE_API_URL" == "$BACKEND_URL" ]; then
        echo -e "Mobile app .env: ${GREEN}✓ Matches backend URL${NC}"
    else
        echo -e "Mobile app .env: ${YELLOW}⚠ Mismatch!${NC}"
        echo "  Expected: $BACKEND_URL"
        echo "  Found: $MOBILE_API_URL"
    fi
else
    echo -e "Mobile app .env: ${YELLOW}⚠ File not found${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Open frontend and sign in with: controller / control123"
echo "2. Open mobile app and use 'Test connection'"
echo "3. File a test report from mobile app"
echo "4. Verify it appears in the frontend Incidents page"
echo ""
echo -e "${YELLOW}Important:${NC} For production, remember to:"
echo "- Set NER_DISABLE_DEMO_SEED=1 on Render"
echo "- Update CORS_ORIGINS to your frontend URL"
echo "- Create real user accounts (see DEPLOYMENT_CHECKLIST.md)"
echo ""
