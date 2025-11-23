# Options Data Integration Guide

## Overview

This guide explains how to fetch historical options data with Open Interest (OI) and Implied Volatility (IV) from the Dhan API for "Smart Money" sentiment analysis.

## What You Can Get

- **Historical Expired Options Data**: Last 5 years
- **Data Fields**: Open, High, Low, Close, Volume, **Open Interest (OI)**, **Implied Volatility (IV)**
- **Strike Selection**: ATM (At The Money), ITM (In The Money), OTM (Out The Money)
- **Option Types**: Call (CE) or Put (PE)

## Dhan API Endpoint

The Dhan API provides a `/charts/rollingoption` endpoint for historical rolling options data.

**Key Advantage**: You don't need to guess specific Symbol IDs for expired contracts. You can request data based on "Strike relative to ATM" (e.g., "Give me the ATM Call option data for NIFTY from Jan 2023").

## Usage

### Basic Usage

```bash
python3 legacy_scripts/fetch_options_data.py NIFTY \
    --strike-type ATM \
    --option-type CE \
    --from-date 2023-01-01 \
    --to-date 2023-12-31 \
    --output-dir analysis_results/NIFTY/options_data
```

### Parameters

- `symbol`: Underlying symbol (e.g., NIFTY, BANKNIFTY, RELIANCE)
- `--strike-type`: ATM, ITM, or OTM
- `--option-type`: CE (Call) or PE (Put)
- `--from-date`: Start date (YYYY-MM-DD)
- `--to-date`: End date (YYYY-MM-DD)
- `--output-dir`: Optional output directory

## Implementation Notes

### Current Status

The `dhanhq` Python client doesn't expose a direct method for the rolling options endpoint. The script attempts to:

1. **Primary Method**: Make direct HTTP request to `/charts/rollingoption` endpoint
2. **Fallback**: Use `option_chain` method to build historical series (not yet implemented)

### API Endpoint Details

**✅ Verified**: Based on [Dhan API v2 Documentation](https://dhanhq.co/docs/v2/expired-options-data/):

- **Endpoint**: `POST https://api.dhan.co/v2/charts/rollingoption`
- **Method**: POST (not GET)
- **Authentication**: `access-token` header
- **Request Body**: JSON with specific structure (see below)

**Current Status**: Endpoint is correct, but requires valid access token (401 Unauthorized indicates authentication issue).

1. **Different Base URL**: May be one of:
   - `https://api.dhan.co/api/charts/rollingoption`
   - `https://api.dhan.co/v1/charts/rollingoption`
   - `https://api.dhan.co/charts/rollingoption` (tested - 404)
   - Different base URL entirely

2. **Different Path**: May be:
   - `/api/rollingoption`
   - `/v1/rollingoption`
   - `/options/rolling`
   - Different path structure

3. **Access Method**: May require:
   - Different authentication method
   - Access via dhanhq client's internal HTTP methods
   - Different parameter format

**Recommended Steps**:
1. Check Dhan API documentation for the exact endpoint
2. Verify with Dhan support if endpoint exists
3. Check if endpoint requires specific API version
4. Verify authentication method (may need session token vs access token)

**Request Structure** (from documentation):
```json
{
    "exchangeSegment": "NSE_FNO",
    "interval": 1,
    "securityId": 13,
    "instrument": "OPTIDX",
    "expiryFlag": "MONTH",
    "expiryCode": 1,
    "strike": "ATM",
    "drvOptionType": "CALL",
    "requiredData": ["open", "high", "low", "close", "volume", "iv", "oi", "strike", "spot"],
    "fromDate": "2021-08-01",
    "toDate": "2021-09-01"
}
```

**Response Structure**:
- Returns arrays for each field (open, high, low, close, volume, iv, oi, strike, spot, timestamp)
- Data is organized by option type (ce/pe)
- Timestamps are Unix epoch (seconds)

### Verification Steps

1. Check Dhan API documentation for exact endpoint URL
2. Verify parameter names and formats
3. Test with a small date range first
4. Verify response format (JSON structure)

## Integration with Pattern Analysis

Once options data is fetched, you can extend the pattern analysis to include:

### Smart Money Sentiment Patterns

1. **OI-Based Patterns**:
   - OI accumulation (increasing OI with price movement)
   - OI distribution (decreasing OI with price movement)
   - OI divergence (price vs OI mismatch)

2. **IV-Based Patterns**:
   - IV spikes (fear/volatility events)
   - IV compression (low volatility periods)
   - IV skew patterns (Call vs Put IV differences)

3. **Combined Price-OI-IV Patterns**:
   - High OI + High IV + Price movement (smart money activity)
   - Low OI + Low IV + Price movement (retail activity)
   - OI buildup before major moves

### Example Integration

```python
# Load options data
options_df = pd.read_csv('NIFTY_CE_ATM_options_2023-01-01_to_2023-12-31.csv', index_col=0, parse_dates=True)

# Combine with underlying price data
underlying_df = pd.read_csv('NIFTY_intraday_1min_raw.csv', index_col=0, parse_dates=True)

# Analyze OI changes
options_df['OI_Change'] = options_df['OI'].pct_change()
options_df['OI_Z'] = (options_df['OI'] - options_df['OI'].rolling(20).mean()) / options_df['OI'].rolling(20).std()

# Detect smart money patterns
options_df['Smart_Money_Buy'] = (options_df['OI_Change'] > 0.1) & (options_df['IV'] < options_df['IV'].rolling(20).mean())
options_df['Smart_Money_Sell'] = (options_df['OI_Change'] < -0.1) & (options_df['IV'] > options_df['IV'].rolling(20).mean())
```

## Troubleshooting

### Issue: HTTP 401 Unauthorized - "Client ID or user generated access token is invalid or expired"

**Possible Causes**:
1. **V2 API Token Requirement**: The v2 API (`/v2/charts/rollingoption`) may require a different type of access token than v1 endpoints
2. **Token Generation**: The token may need to be generated specifically for v2 API access
3. **Client ID Mismatch**: The Client ID in the token payload must match the Client ID used in the request
4. **Token Consumer Type**: The token's `tokenConsumerType` may need to be different for v2 endpoints

**Solutions**:
1. **Generate New Token**: Generate a new access token from Dhan API dashboard, ensuring it's for v2 API
2. **Check Token Scope**: Verify the token has permissions for options data access
3. **Use dhanhq Client Methods**: If available, use dhanhq client's internal methods which may handle v2 authentication automatically
4. **Contact Dhan Support**: If the issue persists, contact Dhan support to verify v2 API token requirements

**Note**: The token expiration check shows the token is valid, and the same token works for v1 endpoints (intraday data). This suggests:

1. **V2 API Permissions**: The v2 endpoint (`/v2/charts/rollingoption`) may require the token to have specific v2 API permissions/scopes
2. **Token Scope**: Your current token may only have access to v1 endpoints (historical_daily_data, intraday_minute_data) but not v2 endpoints
3. **API Version**: The v2 API might require a separate token generation or subscription

**Solution**: Contact Dhan support to:
- Verify if your account has access to v2 API endpoints
- Check if a separate token or permission is needed for `/v2/charts/rollingoption`
- Confirm if v2 endpoints require a different subscription tier

The code implementation is correct and uses the same authentication method as the working intraday data endpoints.

### Issue: HTTP 404 Not Found

**Solution**: 
- Verify the endpoint URL is correct
- Check if the endpoint requires different base URL
- Verify API documentation for correct endpoint path

### Issue: No Data Returned

**Solution**:
- Check date range (may be limited to certain periods)
- Verify symbol format (may need specific format)
- Check if strike_type parameter format is correct
- Verify option_type is CE or PE

### Issue: Method Not Found

**Solution**: The `dhanhq` client may not have this method. Use the HTTP endpoint approach instead.

## Next Steps

1. **Verify Endpoint**: Test the `/charts/rollingoption` endpoint with Dhan API documentation
2. **Test Fetching**: Run the script with a small date range to verify it works
3. **Extend Analysis**: Add options-specific patterns to `simple_intraday_analysis.py`
4. **Combine Data**: Integrate options data with underlying price data for comprehensive analysis

## References

- Dhan API Documentation: Check for `/charts/rollingoption` endpoint details
- Dhan Scrip Master: Required for symbol-to-security-ID mapping
- Options Data Format: Verify response structure matches expected format

