#!/usr/bin/env python3
"""
Simple Orchestrator for Multi-Asset Streaming

This orchestrator manages separate processes for each asset type,
aligning with Polygon.io's one-connection-per-cluster architecture.

Usage:
    # Stream all available assets
    python src/data/stream_orchestrator.py
    
    # Stream specific assets
    python src/data/stream_orchestrator.py --assets stocks crypto
"""

import argparse
import subprocess
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Asset stream configurations
STREAM_CONFIGS = {
    'stocks': {
        'script': 'src/data/stream_stocks.py',
        'name': '📈 Stock Stream',
        'market_hours': True,  # Only runs during market hours
        'schedule': {
            'start': '09:30',
            'end': '16:00',
            'timezone': 'America/New_York'
        }
    },
    'crypto': {
        'script': 'src/data/stream_crypto.py', 
        'name': '💰 Crypto Stream',
        'market_hours': False  # Runs 24/7
    }
}

class StreamOrchestrator:
    """Orchestrate multiple asset streams in separate processes"""
    
    def __init__(self, assets: Optional[list] = None):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
        # Determine which assets to stream
        if assets:
            self.assets = [a for a in assets if a in STREAM_CONFIGS]
        else:
            # Default to all available
            self.assets = list(STREAM_CONFIGS.keys())
        
        print(f"🎼 Stream Orchestrator initialized")
        print(f"📊 Assets to stream: {', '.join(self.assets)}\n")
    
    def start_stream(self, asset: str) -> Optional[subprocess.Popen]:
        """Start a single asset stream"""
        config = STREAM_CONFIGS[asset]
        
        # Check market hours if applicable
        if config.get('market_hours') and not self.is_market_open(config.get('schedule')):
            print(f"⏰ {config['name']} - Market closed, skipping")
            return None
        
        print(f"🚀 Starting {config['name']}...")
        try:
            proc = subprocess.Popen(
                [sys.executable, config['script']],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes[asset] = proc
            return proc
        except Exception as e:
            print(f"❌ Failed to start {asset}: {e}")
            return None
    
    def is_market_open(self, schedule: Optional[dict]) -> bool:
        """Check if market is currently open"""
        if not schedule:
            return True
        
        # For now, simplified check (you'd want pytz for proper timezone handling)
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        # Basic check (doesn't account for weekends/holidays)
        return schedule['start'] <= current_time <= schedule['end']
    
    def monitor_streams(self):
        """Monitor and restart streams if needed"""
        while self.running:
            for asset in self.assets:
                config = STREAM_CONFIGS[asset]
                proc = self.processes.get(asset)
                
                # Check if process needs to be started or restarted
                if proc is None or proc.poll() is not None:
                    # Check market hours
                    if config.get('market_hours') and not self.is_market_open(config.get('schedule')):
                        continue
                    
                    if proc and proc.poll() is not None:
                        print(f"⚠️  {config['name']} stopped (exit code: {proc.returncode}), restarting...")
                    
                    self.start_stream(asset)
                
                # Read and display output
                if proc and proc.poll() is None:
                    try:
                        line = proc.stdout.readline()
                        if line:
                            print(f"[{asset}] {line.strip()}")
                    except:
                        pass
            
            time.sleep(1)
    
    def start(self):
        """Start all configured streams"""
        self.running = True
        
        # Start initial streams
        for asset in self.assets:
            self.start_stream(asset)
        
        # Monitor streams
        try:
            self.monitor_streams()
        except KeyboardInterrupt:
            print("\n🛑 Orchestrator interrupted")
        finally:
            self.stop()
    
    def stop(self):
        """Stop all streams gracefully"""
        self.running = False
        print("\n📴 Stopping all streams...")
        
        for asset, proc in self.processes.items():
            if proc and proc.poll() is None:
                print(f"   Stopping {STREAM_CONFIGS[asset]['name']}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        
        print("✅ All streams stopped")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Multi-asset stream orchestrator')
    parser.add_argument(
        '--assets',
        nargs='+',
        choices=list(STREAM_CONFIGS.keys()),
        help='Asset types to stream (default: all)'
    )
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = StreamOrchestrator(args.assets)
    
    # Handle signals
    def signal_handler(sig, frame):
        orchestrator.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start streaming
    orchestrator.start()

if __name__ == "__main__":
    main()