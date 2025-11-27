"""
Dhan Market Depth WebSocket Client

Connects to Dhan WebSocket API for real-time Full Market Depth data (20-level or 200-level).
This data can be used to detect demand/supply zones and build trading systems.

Usage:
    python3 market_depth_websocket.py --level 20 --instruments NSE_EQ:1333 NSE_EQ:11536
    python3 market_depth_websocket.py --level 200 --instruments NSE_EQ:1333
"""

import os
import sys
import json
import struct
import argparse
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import time

try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dhan API Configuration
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "1109130648")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY0MzQ2ODkzLCJpYXQiOjE3NjQyNjA0OTMsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA5MTMwNjQ4In0.iJstgOK6mjdWKAgqPEiB1nHC0qf66BiEm1Ktr4Hj238ywZa0jQ8_MnosdDyE_cAqox2w3eo48iEjxT9HhdmRsw")


class MarketDepthWebSocket:
    """WebSocket client for Dhan Market Depth data."""
    
    # Feed Response Codes
    RESPONSE_CODE_BID = 41  # Bid data (Buy)
    RESPONSE_CODE_ASK = 51  # Ask data (Sell)
    RESPONSE_CODE_DISCONNECT = 50
    
    # Request Codes
    REQUEST_CODE_SUBSCRIBE = 23
    REQUEST_CODE_DISCONNECT = 12
    
    def __init__(self, client_id, access_token, level=20):
        """
        Initialize Market Depth WebSocket client.
        
        Args:
            client_id (str): Dhan client ID
            access_token (str): Dhan access token
            level (int): Market depth level - 20 or 200
        """
        self.client_id = client_id
        self.access_token = access_token
        self.level = level
        self.ws = None
        self.connected = False
        self.depth_data = {}  # Store depth data by security_id
        self.logger = logging.getLogger(__name__)
        
        # WebSocket endpoint based on level
        if level == 20:
            self.endpoint = f"wss://depth-api-feed.dhan.co/twentydepth?token={access_token}&clientId={client_id}&authType=2"
        elif level == 200:
            self.endpoint = f"wss://full-depth-api.dhan.co/twohundreddepth?token={access_token}&clientId={client_id}&authType=2"
        else:
            raise ValueError("Level must be 20 or 200")
    
    def connect(self):
        """Establish WebSocket connection."""
        try:
            self.logger.info(f"Connecting to Market Depth WebSocket (Level {self.level})...")
            self.logger.info(f"Endpoint: {self.endpoint[:80]}...")
            
            # Create WebSocket connection
            self.ws = websocket.WebSocketApp(
                self.endpoint,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Run WebSocket in a separate thread
            self.ws.run_forever()
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise
    
    def _on_open(self, ws):
        """Called when WebSocket connection is opened."""
        self.connected = True
        self.logger.info("✅ WebSocket connection established")
        self.logger.info("   Connection will be kept alive with ping/pong (every 10 seconds)")
        self.logger.info("   ⚠️  Note: Market depth data is only available during market hours")
        self.logger.info("      (NSE: 9:15 AM - 3:30 PM IST, Monday-Friday)")
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages (binary data)."""
        try:
            # Log message info
            if isinstance(message, bytes):
                self.logger.debug(f"Received binary message: {len(message)} bytes")
            else:
                self.logger.debug(f"Received message (type: {type(message)}): {message[:100] if len(str(message)) > 100 else message}")
            
            # Parse binary message
            self._parse_depth_packet(message)
        except Exception as e:
            self.logger.error(f"Error parsing message: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        self.logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        self.connected = False
        self.logger.info(f"WebSocket connection closed (code: {close_status_code}, msg: {close_msg})")
    
    def _parse_depth_packet(self, message):
        """
        Parse binary depth packet.
        
        Structure:
        - Header (12 bytes): Message Length, Response Code, Exchange Segment, Security ID, Sequence
        - Depth Data: Multiple packets of 16 bytes each (Price, Quantity, No. of Orders)
        
        Note: Packets are stacked when multiple instruments are subscribed.
        """
        try:
            offset = 0
            message_length = len(message)
            
            while offset < message_length:
                # Parse response header (12 bytes)
                if offset + 12 > message_length:
                    break
                
                # Bytes 1-2: Message Length (int16, little-endian)
                # This is the total length of this packet including header
                msg_len = struct.unpack('<h', message[offset:offset+2])[0]
                
                # Byte 3: Feed Response Code
                response_code = struct.unpack('B', message[offset+2:offset+3])[0]
                
                # Byte 4: Exchange Segment
                exchange_segment = struct.unpack('B', message[offset+3:offset+4])[0]
                
                # Bytes 5-8: Security ID (int32, little-endian)
                security_id = struct.unpack('<i', message[offset+4:offset+8])[0]
                
                # Bytes 9-12: Sequence/No. of Rows (uint32, little-endian)
                # For 20-level: sequence number, for 200-level: number of rows
                num_rows = struct.unpack('<I', message[offset+8:offset+12])[0]
                
                # Check for disconnection
                if response_code == self.RESPONSE_CODE_DISCONNECT:
                    if offset + 14 <= message_length:
                        disconnect_code = struct.unpack('<h', message[offset+12:offset+14])[0]
                        self.logger.warning(f"Disconnection received (code: {disconnect_code})")
                    return
                
                # Parse depth data (Bid or Ask)
                if response_code in [self.RESPONSE_CODE_BID, self.RESPONSE_CODE_ASK]:
                    depth_type = "Bid" if response_code == self.RESPONSE_CODE_BID else "Ask"
                    
                    # Calculate number of depth levels
                    # For 20-level: always 20 packets, for 200-level: use num_rows
                    if self.level == 20:
                        num_levels = 20
                    else:
                        num_levels = num_rows if num_rows > 0 else 200
                    
                    # Calculate data length: header (12) + depth packets (num_levels * 16)
                    expected_packet_length = 12 + (num_levels * 16)
                    
                    # Parse depth packets (16 bytes each: Price, Quantity, No. of Orders)
                    depth_data = []
                    data_offset = offset + 12
                    
                    for i in range(num_levels):
                        if data_offset + 16 > message_length or data_offset + 16 > offset + expected_packet_length:
                            break
                        
                        # Bytes 1-8: Price (float64, little-endian)
                        price = struct.unpack('<d', message[data_offset:data_offset+8])[0]
                        
                        # Bytes 9-12: Quantity (uint32, little-endian)
                        quantity = struct.unpack('<I', message[data_offset+8:data_offset+12])[0]
                        
                        # Bytes 13-16: No. of Orders (uint32, little-endian)
                        num_orders = struct.unpack('<I', message[data_offset+12:data_offset+16])[0]
                        
                        if price > 0:  # Only add non-zero prices
                            depth_data.append({
                                'Level': i + 1,
                                'Price': price,
                                'Quantity': quantity,
                                'Orders': num_orders
                            })
                        
                        data_offset += 16
                    
                    # Store depth data
                    if security_id not in self.depth_data:
                        self.depth_data[security_id] = {
                            'exchange_segment': exchange_segment,
                            'bid': [],
                            'ask': [],
                            'timestamp': datetime.now()
                        }
                    
                    self.depth_data[security_id][depth_type.lower()] = depth_data
                    self.depth_data[security_id]['timestamp'] = datetime.now()
                    
                    # Log depth update
                    if len(depth_data) > 0:
                        self.logger.info(f"📊 {depth_type} depth updated for Security ID {security_id}: "
                                        f"{len(depth_data)} levels")
                        # Log top 3 levels
                        top_levels = depth_data[:3]
                        for level in top_levels:
                            self.logger.info(f"   Level {level['Level']}: Price={level['Price']:.2f}, "
                                           f"Qty={level['Quantity']}, Orders={level['Orders']}")
                
                # Move to next packet using message length from header
                # If msg_len is valid, use it; otherwise calculate from parsed data
                if msg_len > 0 and msg_len <= message_length - offset:
                    offset += msg_len
                else:
                    # Fallback: calculate from parsed data
                    if self.level == 20:
                        offset += 12 + (20 * 16)  # Header + 20 levels
                    else:
                        offset += 12 + (num_rows * 16)  # Header + num_rows levels
                
        except Exception as e:
            self.logger.error(f"Error parsing depth packet: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    def subscribe(self, instruments):
        """
        Subscribe to market depth for instruments.
        
        Args:
            instruments (list): List of tuples (exchange_segment, security_id) or dicts
        """
        if not self.connected:
            self.logger.error("Not connected. Call connect() first.")
            return
        
        try:
            # Format instruments
            if self.level == 20:
                # 20-level: Can subscribe to up to 50 instruments
                if len(instruments) > 50:
                    self.logger.warning(f"20-level depth supports max 50 instruments. Subscribing to first 50.")
                    instruments = instruments[:50]
                
                instrument_list = []
                for inst in instruments:
                    if isinstance(inst, tuple):
                        exchange_segment, security_id = inst
                    elif isinstance(inst, dict):
                        exchange_segment = inst['ExchangeSegment']
                        security_id = inst['SecurityId']
                    else:
                        continue
                    
                    instrument_list.append({
                        "ExchangeSegment": exchange_segment,
                        "SecurityId": str(security_id)
                    })
                
                request = {
                    "RequestCode": self.REQUEST_CODE_SUBSCRIBE,
                    "InstrumentCount": len(instrument_list),
                    "InstrumentList": instrument_list
                }
            else:
                # 200-level: Only 1 instrument per connection
                if len(instruments) > 1:
                    self.logger.warning(f"200-level depth supports only 1 instrument. Using first instrument.")
                    instruments = [instruments[0]]
                
                inst = instruments[0]
                if isinstance(inst, tuple):
                    exchange_segment, security_id = inst
                elif isinstance(inst, dict):
                    exchange_segment = inst['ExchangeSegment']
                    security_id = inst['SecurityId']
                else:
                    return
                
                request = {
                    "RequestCode": self.REQUEST_CODE_SUBSCRIBE,
                    "ExchangeSegment": exchange_segment,
                    "SecurityId": str(security_id)
                }
            
            # Send subscription request
            request_json = json.dumps(request)
            self.ws.send(request_json)
            self.logger.info(f"✅ Subscribed to {len(instruments)} instrument(s)")
            self.logger.debug(f"Request: {request_json}")
            
        except Exception as e:
            self.logger.error(f"Error subscribing: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
    
    def get_depth_dataframe(self, security_id):
        """
        Get market depth data as DataFrame.
        
        Args:
            security_id (int): Security ID
            
        Returns:
            pandas.DataFrame: Market depth data with Bid and Ask levels
        """
        if security_id not in self.depth_data:
            return pd.DataFrame()
        
        data = self.depth_data[security_id]
        bid_df = pd.DataFrame(data['bid'])
        ask_df = pd.DataFrame(data['ask'])
        
        # Combine bid and ask
        if not bid_df.empty:
            bid_df['Type'] = 'Bid'
        if not ask_df.empty:
            ask_df['Type'] = 'Ask'
        
        if not bid_df.empty and not ask_df.empty:
            df = pd.concat([bid_df, ask_df], ignore_index=True)
        elif not bid_df.empty:
            df = bid_df
        elif not ask_df.empty:
            df = ask_df
        else:
            return pd.DataFrame()
        
        df['SecurityId'] = security_id
        df['Timestamp'] = data['timestamp']
        
        return df
    
    def disconnect(self):
        """Disconnect WebSocket."""
        if self.ws and self.connected:
            try:
                disconnect_request = {"RequestCode": self.REQUEST_CODE_DISCONNECT}
                self.ws.send(json.dumps(disconnect_request))
                self.ws.close()
                self.logger.info("Disconnected from WebSocket")
            except Exception as e:
                self.logger.error(f"Error disconnecting: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Dhan Market Depth WebSocket Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 20-level depth for multiple instruments
  python3 market_depth_websocket.py --level 20 --instruments NSE_EQ:1333 NSE_EQ:11536
  
  # 200-level depth for single instrument
  python3 market_depth_websocket.py --level 200 --instruments NSE_EQ:1333
        """
    )
    
    parser.add_argument('--level', type=int, choices=[20, 200], default=20,
                       help='Market depth level: 20 or 200 (default: 20)')
    parser.add_argument('--instruments', nargs='+', required=True,
                       help='Instruments in format: EXCHANGE_SEGMENT:SECURITY_ID (e.g., NSE_EQ:1333)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Connection duration in seconds (default: 60)')
    parser.add_argument('--output-dir', help='Output directory to save depth data')
    
    args = parser.parse_args()
    
    if not WEBSOCKET_AVAILABLE:
        logger.error("websocket-client library not available. Install with: pip install websocket-client")
        return
    
    # Parse instruments
    instruments = []
    for inst_str in args.instruments:
        try:
            exchange_segment, security_id = inst_str.split(':')
            instruments.append((exchange_segment, security_id))
        except ValueError:
            logger.error(f"Invalid instrument format: {inst_str}. Use EXCHANGE_SEGMENT:SECURITY_ID")
            return
    
    # Create WebSocket client
    client = MarketDepthWebSocket(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN, level=args.level)
    
    # Connect and subscribe
    try:
        # Start connection in a thread
        import threading
        ws_thread = threading.Thread(target=client.connect, daemon=True)
        ws_thread.start()
        
        # Wait for connection
        time.sleep(2)
        
        if client.connected:
            # Subscribe to instruments
            client.subscribe(instruments)
            
            # Keep connection alive for specified duration
            logger.info(f"Receiving market depth data for {args.duration} seconds...")
            logger.info("   (If no data is received, markets may be closed)")
            
            # Monitor for data updates
            start_time = time.time()
            last_update_time = start_time
            update_count = 0
            
            while time.time() - start_time < args.duration:
                time.sleep(1)
                
                # Check for new data
                current_count = sum(len(data.get('bid', [])) + len(data.get('ask', [])) 
                                   for data in client.depth_data.values())
                if current_count > update_count:
                    update_count = current_count
                    last_update_time = time.time()
                    logger.info(f"   📊 Received depth data updates (total levels: {update_count})")
            
            # Check if we received any data
            total_data = sum(len(data.get('bid', [])) + len(data.get('ask', [])) 
                           for data in client.depth_data.values())
            
            if total_data == 0:
                logger.warning("⚠️  No market depth data received.")
                logger.warning("   Possible reasons:")
                logger.warning("   1. Markets are closed (NSE: 9:15 AM - 3:30 PM IST, Mon-Fri)")
                logger.warning("   2. Instrument is not tradeable")
                logger.warning("   3. Subscription request format issue")
            else:
                logger.info(f"✅ Received depth data for {len(client.depth_data)} instrument(s)")
            
            # Save data if output directory specified
            if args.output_dir:
                os.makedirs(args.output_dir, exist_ok=True)
                saved_count = 0
                for security_id in client.depth_data.keys():
                    df = client.get_depth_dataframe(security_id)
                    if not df.empty:
                        filename = os.path.join(args.output_dir, f"depth_{security_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                        df.to_csv(filename, index=False)
                        logger.info(f"💾 Saved depth data to {filename} ({len(df)} rows)")
                        saved_count += 1
                
                if saved_count == 0:
                    logger.info("   No data to save (markets may be closed)")
            
            # Disconnect
            client.disconnect()
        else:
            logger.error("Failed to establish WebSocket connection")
            
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        client.disconnect()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        client.disconnect()


if __name__ == "__main__":
    main()

