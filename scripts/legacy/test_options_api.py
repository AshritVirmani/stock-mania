"""
Test Dhan API for Options Data Endpoints

Explores available methods in dhanhq client for fetching historical options data.
"""

import os
import sys

try:
    from dhanhq import dhanhq
    DHAN_AVAILABLE = True
except ImportError:
    print("❌ dhanhq not available")
    sys.exit(1)

# Dhan API Configuration
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "1109130648")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzYzOTY1ODM1LCJpYXQiOjE3NjM4Nzk0MzUsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMSUYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsZW50SWQiOjExMDkxMzA2NDh9.YRHIEqoabzTLwde29P8g6ZKGpG9gWI4YpfJ2Ge5yDcn_cxzFLOXslEZ-5PY2HPGdTJPpQDGRK6YUOUi1pkzWvg")

print("="*80)
print("🔍 EXPLORING DHAN API FOR OPTIONS DATA")
print("="*80)

# Initialize client
dhan = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)

# Get all methods
all_methods = [m for m in dir(dhan) if not m.startswith('_') and callable(getattr(dhan, m))]

print("\n📋 All available methods:")
print("-" * 80)
for method in sorted(all_methods):
    print(f"  - {method}")

# Filter for options/rolling related
options_methods = [m for m in all_methods if any(keyword in m.lower() for keyword in ['option', 'rolling', 'oi', 'iv', 'volatility'])]
print("\n🎯 Options/Rolling related methods:")
print("-" * 80)
if options_methods:
    for method in options_methods:
        print(f"  ✅ {method}")
        # Try to get method signature
        try:
            import inspect
            sig = inspect.signature(getattr(dhan, method))
            print(f"     Signature: {sig}")
        except:
            pass
else:
    print("  ❌ No options-specific methods found")

# Check option_chain method
print("\n📊 Testing option_chain method:")
print("-" * 80)
if hasattr(dhan, 'option_chain'):
    try:
        # Try to see what parameters it accepts
        import inspect
        sig = inspect.signature(dhan.option_chain)
        print(f"  Signature: {sig}")
        print(f"  Parameters: {list(sig.parameters.keys())}")
    except Exception as e:
        print(f"  Error inspecting signature: {e}")

# Check if there's a way to access HTTP endpoints directly
print("\n🌐 Checking for HTTP/API access methods:")
print("-" * 80)
http_methods = [m for m in all_methods if any(keyword in m.lower() for keyword in ['http', 'request', 'api', 'get', 'post'])]
if http_methods:
    for method in http_methods:
        print(f"  - {method}")
else:
    print("  No direct HTTP methods found")

# Check client attributes for base URL or API info
print("\n🔗 Checking client attributes:")
print("-" * 80)
attrs = [a for a in dir(dhan) if not a.startswith('_') and not callable(getattr(dhan, a))]
for attr in attrs[:10]:  # Show first 10
    try:
        val = getattr(dhan, attr)
        if not isinstance(val, (int, float, str, bool)) or len(str(val)) < 100:
            print(f"  {attr}: {val}")
    except:
        pass

print("\n" + "="*80)
print("💡 RECOMMENDATIONS:")
print("="*80)
print("1. Check Dhan API documentation for '/charts/rollingoption' endpoint")
print("2. If endpoint exists but method doesn't, may need to:")
print("   - Use requests library to call endpoint directly")
print("   - Check if dhanhq library needs update")
print("   - Use option_chain and build historical series manually")
print("="*80)

