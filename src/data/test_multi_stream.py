#!/usr/bin/env python3
"""
Simple test to verify we can run multiple WebSocket streams simultaneously
"""

import threading
import time
import subprocess
import signal
import sys

def run_stocks():
    """Run stock streaming in subprocess"""
    print("Starting stock stream...")
    proc = subprocess.Popen([
        sys.executable, 
        "src/data/stream_stocks.py"
    ])
    return proc

def run_crypto():
    """Run crypto streaming in subprocess"""
    print("Starting crypto stream...")
    proc = subprocess.Popen([
        sys.executable, 
        "src/data/stream_crypto.py"
    ])
    return proc

def main():
    """Test running both streams simultaneously"""
    print("Testing multi-asset streaming...")
    print("This will run stocks and crypto streams in separate processes")
    print("Press Ctrl+C to stop\n")
    
    # Start both streams
    stock_proc = run_stocks()
    time.sleep(2)  # Give stocks time to connect
    crypto_proc = run_crypto()
    
    try:
        # Monitor processes
        while True:
            # Check if processes are still running
            if stock_proc.poll() is not None:
                print("Stock stream died, restarting...")
                stock_proc = run_stocks()
            
            if crypto_proc.poll() is not None:
                print("Crypto stream died, restarting...")
                crypto_proc = run_crypto()
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nStopping streams...")
        stock_proc.terminate()
        crypto_proc.terminate()
        
        # Wait for clean shutdown
        stock_proc.wait(timeout=5)
        crypto_proc.wait(timeout=5)
        
        print("All streams stopped")

if __name__ == "__main__":
    main()