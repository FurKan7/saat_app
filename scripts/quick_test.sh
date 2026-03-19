#!/bin/bash
# Quick API test script

API_URL="${API_URL:-http://localhost:8000}"

echo "🧪 Quick API Tests"
echo "=================="
echo "API URL: $API_URL"
echo ""

# Test health
echo "1. Testing health endpoint..."
curl -s $API_URL/health | jq '.' || echo "❌ Health check failed"
echo ""

# Test watch list
echo "2. Testing watch list (limit 3)..."
curl -s "$API_URL/watches?limit=3" | jq '.watches | length' || echo "❌ Watch list failed"
echo ""

# Test watch detail
echo "3. Testing watch detail (ID 1)..."
curl -s "$API_URL/watches/1" | jq '.watch_id' || echo "❌ Watch detail failed"
echo ""

# Test watch specs
echo "4. Testing watch specs (ID 1)..."
curl -s "$API_URL/watches/1/specs" | jq '.specs | length' || echo "❌ Watch specs failed"
echo ""

# Test search
echo "5. Testing search (query: Seiko)..."
curl -s "$API_URL/watches?query=Seiko&limit=2" | jq '.watches | length' || echo "❌ Search failed"
echo ""

echo "✅ Quick tests complete!"
echo ""
echo "For full testing, see TESTING.md"
