"""
WebSocket configuration for different asset types and subscription levels.
Each asset type can have its own subscription tier.
"""

import os
from typing import Dict, Optional, List
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AssetType(Enum):
    """Supported asset types"""
    STOCKS = "stocks"
    CRYPTO = "crypto" 
    FOREX = "forex"
    INDICES = "indices"
    OPTIONS = "options"
    FUTURES = "futures"

class SubscriptionTier(Enum):
    """Polygon.io subscription tiers per asset type"""
    BASIC = "basic"           # Free - no WebSocket
    STARTER = "starter"       # Paid - 15min delayed WebSocket
    DEVELOPER = "developer"   # Paid - real-time WebSocket
    ADVANCED = "advanced"     # Paid - real-time WebSocket + extras

class WebSocketConfig:
    """Configuration class for WebSocket connections with per-asset subscriptions"""
    
    # WebSocket availability by tier
    WEBSOCKET_ENABLED_TIERS = {
        SubscriptionTier.STARTER,
        SubscriptionTier.DEVELOPER,
        SubscriptionTier.ADVANCED
    }
    
    # WebSocket URLs based on tier (not asset type)
    WEBSOCKET_BASE_URLS = {
        SubscriptionTier.STARTER: "wss://delayed.polygon.io",
        SubscriptionTier.DEVELOPER: "wss://socket.polygon.io",
        SubscriptionTier.ADVANCED: "wss://socket.polygon.io"
    }
    
    # Data types available for each asset type
    DATA_TYPES = {
        AssetType.STOCKS: {
            'A': 'aggregates',      # Minute aggregates
            'AM': 'aggregates_min', # Explicit minute aggregates
            'AS': 'aggregates_sec', # Second aggregates (Developer+)
            'T': 'trades',          # Individual trades (Developer+)
            'Q': 'quotes',          # Bid/ask quotes (Developer+)
        },
        AssetType.CRYPTO: {
            'XA': 'aggregates',     # Crypto aggregates
            'XAS': 'aggregates_sec',# Crypto second aggregates (Developer+)
            'XT': 'trades',         # Crypto trades (Developer+)
            'XQ': 'quotes',         # Crypto quotes (Developer+)
            'XL2': 'level2'         # Level 2 book data (Advanced+)
        },
        AssetType.FOREX: {
            'C': 'quotes',          # Forex quotes
            'CA': 'aggregates'      # Forex aggregates
        },
        AssetType.INDICES: {
            'I:SPX': 'value',       # Index values (example: S&P 500)
            'V': 'value',           # Index values
            'A': 'aggregates'       # Index aggregates
        },
        AssetType.OPTIONS: {
            'T': 'trades',          # Options trades (Developer+)
            'Q': 'quotes',          # Options quotes (Developer+)
            'A': 'aggregates'       # Options aggregates
        },
        AssetType.FUTURES: {
            'A': 'aggregates',      # Futures aggregates
            'T': 'trades',          # Futures trades (Developer+)
            'Q': 'quotes'           # Futures quotes (Developer+)
        }
    }
    
    # Data types requiring specific tiers
    TIER_RESTRICTED_DATA_TYPES = {
        'AS': SubscriptionTier.DEVELOPER,  # Second aggregates
        'XAS': SubscriptionTier.DEVELOPER,
        'T': SubscriptionTier.DEVELOPER,   # Trades
        'XT': SubscriptionTier.DEVELOPER,
        'Q': SubscriptionTier.DEVELOPER,   # Quotes
        'XQ': SubscriptionTier.DEVELOPER,
        'XL2': SubscriptionTier.ADVANCED   # Level 2
    }
    
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")
        
        # Load per-asset subscription tiers from environment
        self.asset_subscriptions = {}
        for asset_type in AssetType:
            # Look for POLYGON_TIER_STOCKS, POLYGON_TIER_CRYPTO, etc.
            env_key = f"POLYGON_TIER_{asset_type.value.upper()}"
            tier_str = os.getenv(env_key, 'basic')
            
            try:
                self.asset_subscriptions[asset_type] = SubscriptionTier(tier_str.lower())
            except ValueError:
                self.asset_subscriptions[asset_type] = SubscriptionTier.BASIC
                print(f"Warning: Invalid tier '{tier_str}' for {asset_type.value}, defaulting to BASIC")
    
    def has_websocket_access(self, asset_type: AssetType) -> bool:
        """Check if WebSocket access is available for the asset type"""
        tier = self.asset_subscriptions.get(asset_type, SubscriptionTier.BASIC)
        return tier in self.WEBSOCKET_ENABLED_TIERS
    
    def get_subscription_tier(self, asset_type: AssetType) -> SubscriptionTier:
        """Get subscription tier for specific asset type"""
        return self.asset_subscriptions.get(asset_type, SubscriptionTier.BASIC)
    
    def get_websocket_url(self, asset_type: AssetType) -> Optional[str]:
        """Get WebSocket URL for asset type if available"""
        # Check for environment override first
        env_key = f"POLYGON_WS_URL_{asset_type.value.upper()}"
        env_url = os.getenv(env_key)
        if env_url:
            return env_url
        
        # Check if WebSocket is available for this asset type
        tier = self.get_subscription_tier(asset_type)
        if tier not in self.WEBSOCKET_ENABLED_TIERS:
            raise ValueError(f"WebSocket not available for {asset_type.value} on {tier.value} tier. Upgrade to Starter or higher.")
        
        # Special case: Crypto uses real-time endpoint even on Starter tier
        if asset_type == AssetType.CRYPTO and tier == SubscriptionTier.STARTER:
            base_url = self.WEBSOCKET_BASE_URLS.get(SubscriptionTier.DEVELOPER)
        else:
            base_url = self.WEBSOCKET_BASE_URLS.get(tier)
            
        return f"{base_url}/{asset_type.value}"
    
    def get_available_data_types(self, asset_type: AssetType, include_restricted: bool = False) -> Dict[str, str]:
        """Get available data types for asset type based on subscription"""
        all_types = self.DATA_TYPES.get(asset_type, {})
        
        if include_restricted:
            return all_types
        
        # Filter based on subscription tier
        tier = self.get_subscription_tier(asset_type)
        available_types = {}
        
        for code, description in all_types.items():
            required_tier = self.TIER_RESTRICTED_DATA_TYPES.get(code)
            if required_tier is None or self._tier_meets_requirement(tier, required_tier):
                available_types[code] = description
        
        return available_types
    
    def _tier_meets_requirement(self, current_tier: SubscriptionTier, required_tier: SubscriptionTier) -> bool:
        """Check if current tier meets or exceeds requirement"""
        tier_hierarchy = [SubscriptionTier.BASIC, SubscriptionTier.STARTER, 
                         SubscriptionTier.DEVELOPER, SubscriptionTier.ADVANCED]
        
        current_idx = tier_hierarchy.index(current_tier)
        required_idx = tier_hierarchy.index(required_tier)
        
        return current_idx >= required_idx
    
    def get_subscription_channels(self, asset_type: AssetType, symbols: List[str], data_types: List[str] = None) -> List[str]:
        """Build subscription channel strings for WebSocket"""
        # Check WebSocket access first
        if not self.has_websocket_access(asset_type):
            raise ValueError(f"WebSocket not available for {asset_type.value} with {self.get_subscription_tier(asset_type).value} tier")
        
        if data_types is None:
            # Default data types per asset type
            defaults = {
                AssetType.STOCKS: ['A'],      # Minute aggregates
                AssetType.CRYPTO: ['XA'],     # Crypto aggregates  
                AssetType.FOREX: ['C'],       # Forex quotes
                AssetType.INDICES: ['V'],     # Index values
                AssetType.OPTIONS: ['A'],     # Options aggregates
                AssetType.FUTURES: ['A']      # Futures aggregates
            }
            data_types = defaults.get(asset_type, ['A'])
        
        # Validate data types against subscription tier
        available_types = self.get_available_data_types(asset_type)
        for dt in data_types:
            if dt not in available_types:
                tier = self.get_subscription_tier(asset_type)
                raise ValueError(f"Data type '{dt}' not available for {asset_type.value} on {tier.value} tier")
        
        # Build subscription strings
        channels = []
        for data_type in data_types:
            for symbol in symbols:
                channels.append(f"{data_type}.{symbol}")
        
        return channels
    
    def is_realtime_available(self, asset_type: AssetType) -> bool:
        """Check if real-time data is available for asset type"""
        tier = self.get_subscription_tier(asset_type)
        return tier in [SubscriptionTier.DEVELOPER, SubscriptionTier.ADVANCED]
    
    def get_delay_minutes(self, asset_type: AssetType) -> Optional[int]:
        """Get data delay in minutes for asset type"""
        tier = self.get_subscription_tier(asset_type)
        
        if tier == SubscriptionTier.BASIC:
            return None  # No streaming
        elif tier == SubscriptionTier.STARTER:
            # Crypto is real-time even on Starter tier
            if asset_type == AssetType.CRYPTO:
                return 0
            else:
                return 15    # 15-minute delay for stocks
        else:
            return 0     # Real-time
    
    def get_config_summary(self) -> Dict:
        """Get summary of current configuration"""
        summary = {
            'api_key_configured': bool(self.api_key),
            'asset_subscriptions': {}
        }
        
        for asset_type in AssetType:
            tier = self.get_subscription_tier(asset_type)
            has_websocket = self.has_websocket_access(asset_type)
            
            asset_info = {
                'tier': tier.value,
                'websocket_available': has_websocket,
                'data_delay_minutes': self.get_delay_minutes(asset_type) if has_websocket else 'N/A',
                'available_data_types': list(self.get_available_data_types(asset_type).keys()) if has_websocket else []
            }
            
            if has_websocket:
                try:
                    asset_info['websocket_url'] = self.get_websocket_url(asset_type)
                except ValueError:
                    asset_info['websocket_url'] = 'Not available'
            
            summary['asset_subscriptions'][asset_type.value] = asset_info
        
        return summary


# Configuration singleton
_config_instance = None

def get_websocket_config() -> WebSocketConfig:
    """Get global WebSocket configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = WebSocketConfig()
    return _config_instance


# Convenience functions
def get_ws_url(asset_type: AssetType) -> str:
    """Get WebSocket URL for asset type (raises error if not available)"""
    return get_websocket_config().get_websocket_url(asset_type)

def has_websocket_access(asset_type: AssetType) -> bool:
    """Check if WebSocket access is available for asset type"""
    return get_websocket_config().has_websocket_access(asset_type)

def get_subscription_channels(asset_type: AssetType, symbols: List[str], data_types: List[str] = None) -> List[str]:
    """Get subscription channels for symbols"""
    return get_websocket_config().get_subscription_channels(asset_type, symbols, data_types)

def is_realtime(asset_type: AssetType) -> bool:
    """Check if real-time data is available for asset type"""
    return get_websocket_config().is_realtime_available(asset_type)


if __name__ == "__main__":
    # Test configuration
    config = get_websocket_config()
    print("WebSocket Configuration Summary:")
    print("=" * 70)
    
    summary = config.get_config_summary()
    print(f"API Key Configured: {summary['api_key_configured']}")
    print()
    
    for asset, info in summary['asset_subscriptions'].items():
        print(f"{asset.upper()}:")
        print(f"  Subscription Tier: {info['tier']}")
        print(f"  WebSocket Available: {info['websocket_available']}")
        if info['websocket_available']:
            print(f"  Data Delay: {info['data_delay_minutes']} minutes")
            print(f"  WebSocket URL: {info.get('websocket_url', 'N/A')}")
            print(f"  Available Data Types: {info['available_data_types']}")
        print()
    
    # Test specific scenarios
    print("Testing specific scenarios:")
    print("-" * 30)
    
    # Test stocks (should work with Starter)
    try:
        print(f"Stocks WebSocket URL: {get_ws_url(AssetType.STOCKS)}")
        print(f"AAPL channels: {get_subscription_channels(AssetType.STOCKS, ['AAPL'], ['A'])}")
    except ValueError as e:
        print(f"Stocks error: {e}")
    
    print()
    
    # Test crypto (should fail with Basic)
    try:
        print(f"Crypto WebSocket URL: {get_ws_url(AssetType.CRYPTO)}")
    except ValueError as e:
        print(f"Crypto error: {e}")