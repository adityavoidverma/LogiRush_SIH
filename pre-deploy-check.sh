#!/bin/bash
# Pre-deployment validation script
# Run this BEFORE deploying to catch common issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   LogiRush Pre-Deployment Check           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Check if in correct directory
if [ ! -f "README.md" ] || [ ! -d "routeOptimiserBackend" ]; then
    echo -e "${RED}✗ Not in LogiRush root directory${NC}"
    echo "Please run this script from the LogiRush project root"
    exit 1
fi

echo -e "${BLUE}Checking Backend...${NC}"

# Check backend files
if [ ! -f "routeOptimiserBackend/main.py" ]; then
    echo -e "${RED}✗ Backend main.py not found${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Backend main.py exists${NC}"
fi

if [ ! -f "routeOptimiserBackend/requirements.txt" ]; then
    echo -e "${RED}✗ Backend requirements.txt not found${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Backend requirements.txt exists${NC}"
fi

if [ ! -f "routeOptimiserBackend/Dockerfile" ]; then
    echo -e "${RED}✗ Backend Dockerfile not found${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Backend Dockerfile exists${NC}"
fi

if [ ! -f "render.yaml" ]; then
    echo -e "${YELLOW}⚠ render.yaml not found (needed for one-click deploy)${NC}"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓ render.yaml exists${NC}"
fi

echo ""
echo -e "${BLUE}Checking Frontend...${NC}"

# Check frontend files
if [ ! -f "routeOptimiserFrontend/package.json" ]; then
    echo -e "${RED}✗ Frontend package.json not found${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Frontend package.json exists${NC}"
fi

if [ ! -f "routeOptimiserFrontend/vercel.json" ]; then
    echo -e "${YELLOW}⚠ Frontend vercel.json not found${NC}"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓ Frontend vercel.json exists${NC}"
fi

if [ ! -f "routeOptimiserFrontend/vite.config.js" ]; then
    echo -e "${RED}✗ Frontend vite.config.js not found${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Frontend vite.config.js exists${NC}"
fi

# Check if .env exists (shouldn't be committed)
if [ -f "routeOptimiserFrontend/.env" ]; then
    echo -e "${YELLOW}⚠ Frontend .env file exists (should not be committed to git)${NC}"
    ((WARNINGS++))
fi

echo ""
echo -e "${BLUE}Checking Mobile App...${NC}"

if [ ! -f "nerFieldApp/package.json" ]; then
    echo -e "${RED}✗ Mobile app package.json not found${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Mobile app package.json exists${NC}"
fi

if [ ! -f "nerFieldApp/app.json" ]; then
    echo -e "${RED}✗ Mobile app app.json not found${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Mobile app app.json exists${NC}"
fi

# Check if .env exists (shouldn't be committed)
if [ -f "nerFieldApp/.env" ]; then
    echo -e "${YELLOW}⚠ Mobile .env file exists (should not be committed to git)${NC}"
    ((WARNINGS++))
fi

echo ""
echo -e "${BLUE}Checking Git...${NC}"

# Check git status
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}✗ Not a git repository${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Git repository initialized${NC}"
    
    # Check if there's a remote
    if git remote -v | grep -q "origin"; then
        REMOTE_URL=$(git remote get-url origin)
        echo -e "${GREEN}✓ Git remote configured: $REMOTE_URL${NC}"
    else
        echo -e "${YELLOW}⚠ No git remote configured${NC}"
        echo "  Add one with: git remote add origin <your-repo-url>"
        ((WARNINGS++))
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        echo -e "${YELLOW}⚠ Uncommitted changes detected${NC}"
        echo "  Consider committing before deploy"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓ No uncommitted changes${NC}"
    fi
fi

echo ""
echo -e "${BLUE}Checking Dependencies...${NC}"

# Check if Python is installed
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python installed: $PYTHON_VERSION${NC}"
else
    echo -e "${YELLOW}⚠ Python3 not found (not needed for deploy, but useful for testing)${NC}"
    ((WARNINGS++))
fi

# Check if Node is installed
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js installed: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js not found (required for frontend build)${NC}"
    ((ERRORS++))
fi

# Check if npm is installed
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm installed: $NPM_VERSION${NC}"
else
    echo -e "${RED}✗ npm not found (required for frontend build)${NC}"
    ((ERRORS++))
fi

echo ""
echo -e "${BLUE}Checking .gitignore...${NC}"

if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}⚠ No .gitignore file${NC}"
    ((WARNINGS++))
else
    # Check if important files are ignored
    if grep -q "\.env" .gitignore; then
        echo -e "${GREEN}✓ .env files are ignored${NC}"
    else
        echo -e "${YELLOW}⚠ .env files should be in .gitignore${NC}"
        ((WARNINGS++))
    fi
    
    if grep -q "node_modules" .gitignore; then
        echo -e "${GREEN}✓ node_modules are ignored${NC}"
    else
        echo -e "${YELLOW}⚠ node_modules should be in .gitignore${NC}"
        ((WARNINGS++))
    fi
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to deploy.${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Push to GitHub: git push origin main"
    echo "2. Follow QUICK_DEPLOY.md for deployment"
    echo "3. Or use deploy buttons in README.md"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found, but no critical errors.${NC}"
    echo "You can proceed with deployment, but review warnings above."
else
    echo -e "${RED}✗ $ERRORS error(s) and $WARNINGS warning(s) found.${NC}"
    echo "Please fix errors before deploying."
    exit 1
fi

echo ""
echo -e "${BLUE}Quick commands:${NC}"
echo ""
echo "# Test backend locally:"
echo "cd routeOptimiserBackend && python3 -m pip install -r requirements.txt && python3 main.py"
echo ""
echo "# Test frontend locally:"
echo "cd routeOptimiserFrontend && npm install && npm run dev"
echo ""
echo "# Commit and push:"
echo "git add -A && git commit -m 'Ready for deployment' && git push origin main"
echo ""
