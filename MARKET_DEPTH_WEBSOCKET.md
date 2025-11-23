# Market Depth WebSocket Integration Guide

## Overview

This guide explains how to use the Dhan Market Depth WebSocket API for real-time market depth data (20-level or 200-level). This data is useful for detecting demand/supply zones and building trading systems.

## Features

- **20-Level Market Depth**: Up to 50 instruments per connection
- **200-Level Market Depth**: 1 instrument per connection (complete order book)
- **Real-time Streaming**: WebSocket-based real-time data
- **Binary Packet Parsing**: Automatic parsing of binary response packets
- **DataFrame Export**: Convert depth data to pandas DataFrame for analysis

## Installation

```bash
pip install websocket-client pandas numpy
```

## Usage

### Basic Usage (20-Level Depth)

```bash
python3 legacy_scripts/market_depth_websocket.py \
    --level 20 \
    --instruments NSE_EQ:1333 NSE_EQ:11536 \
    --duration 60 \
    --output-dir market_depth_data
```

### 200-Level Depth (Single Instrument)

```bash
python3 legacy_scripts/market_depth_websocket.py \
    --level 200 \
    --instruments NSE_EQ:1333 \
    --duration 60 \
    --output-dir market_depth_data
```

### Parameters

- `--level`: Market depth level - 20 or 200 (default: 20)
- `--instruments`: List of instruments in format `EXCHANGE_SEGMENT:SECURITY_ID`
- `--duration`: Connection duration in seconds (default: 60)
- `--output-dir`: Optional directory to save depth data as CSV

## WebSocket Endpoints

### 20-Level Market Depth
```
wss://depth-api-feed.dhan.co/twentydepth?token={token}&clientId={clientId}&authType=2
```

### 200-Level Market Depth
```
wss://full-depth-api.dhan.co/twohundreddepth?token={token}&clientId={clientId}&authType=2
```

## Request Structure

### 20-Level Subscription (Multiple Instruments)

```json
{
    "RequestCode": 23,
    "InstrumentCount": 2,
    "InstrumentList": [
        {
            "ExchangeSegment": "NSE_EQ",
            "SecurityId": "1333"
        },
        {
            "ExchangeSegment": "NSE_EQ",
            "SecurityId": "11536"
        }
    ]
}
```

### 200-Level Subscription (Single Instrument)

```json
{
    "RequestCode": 23,
    "ExchangeSegment": "NSE_EQ",
    "SecurityId": "1333"
}
```

## Response Structure

### Binary Packet Format

**Header (12 bytes)**:
- Bytes 1-2: Message Length (int16)
- Byte 3: Feed Response Code (41 for Bid, 51 for Ask)
- Byte 4: Exchange Segment
- Bytes 5-8: Security ID (int32)
- Bytes 9-12: Sequence/No. of Rows (uint32)

**Depth Data (16 bytes per level)**:
- Bytes 1-8: Price (float64)
- Bytes 9-12: Quantity (uint32)
- Bytes 13-16: No. of Orders (uint32)

### Parsed DataFrame Format

```python
# Example output DataFrame
   Level    Price  Quantity  Orders   Type  SecurityId            Timestamp
0      1  2450.50      1000       5   Bid       1333  2024-01-15 10:30:00
1      2  2450.25       500       3   Bid       1333  2024-01-15 10:30:00
2      1  2450.75      2000       8   Ask       1333  2024-01-15 10:30:00
3      2  2451.00      1500       6   Ask       1333  2024-01-15 10:30:00
```

## Connection Management

### Keep-Alive

- Server sends ping every 10 seconds
- Client automatically responds with pong
- Connection closes if no response for 40+ seconds

### Disconnect

Send disconnect request:
```json
{
    "RequestCode": 12
}
```

## Use Cases

### 1. Demand/Supply Zone Detection

Analyze depth data to identify:
- Large bid walls (demand zones)
- Large ask walls (supply zones)
- Order book imbalances

### 2. Market Microstructure Analysis

- Order flow analysis
- Liquidity assessment
- Price impact estimation

### 3. Trading System Development

- Order book imbalance strategies
- Market making algorithms
- Execution algorithms

## Limitations

- **20-Level**: Maximum 50 instruments per connection
- **200-Level**: Only 1 instrument per connection
- **Segments**: Only NSE Equity and Derivatives supported
- **Connection Limit**: Maximum 5 concurrent WebSocket connections

## Troubleshooting

### Connection Issues

- Verify access token is valid
- Check client ID matches token
- Ensure network allows WebSocket connections

### Parsing Errors

- Verify binary packet structure matches documentation
- Check message length calculations
- Ensure proper byte order (little-endian)

### Data Issues

- Verify security IDs are correct
- Check exchange segment codes
- Ensure instruments are tradeable

## Example: Analyzing Depth Data

```python
from legacy_scripts.market_depth_websocket import MarketDepthWebSocket
import pandas as pd

# Create client
client = MarketDepthWebSocket(client_id, access_token, level=20)

# Connect and subscribe
client.connect()
client.subscribe([("NSE_EQ", "1333")])

# Get depth data
df = client.get_depth_dataframe(1333)

# Analyze bid-ask spread
bid_best = df[df['Type'] == 'Bid']['Price'].max()
ask_best = df[df['Type'] == 'Ask']['Price'].min()
spread = ask_best - bid_best

print(f"Bid-Ask Spread: {spread}")

# Analyze order book imbalance
bid_volume = df[df['Type'] == 'Bid']['Quantity'].sum()
ask_volume = df[df['Type'] == 'Ask']['Quantity'].sum()
imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)

print(f"Order Book Imbalance: {imbalance:.2%}")
```

## References

- Dhan API Documentation: Market Depth WebSocket
- Exchange Segment Codes: See Annexure
- Security ID Lookup: Use Scrip Master CSV

