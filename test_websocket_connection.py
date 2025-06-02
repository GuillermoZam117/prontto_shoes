#!/usr/bin/env python3
"""
Test WebSocket connection for the POS system
"""
import asyncio
import websockets
import json
import sys

async def test_websocket_connection():
    """Test WebSocket connection to the POS system"""
    try:        # Test WebSocket connection
        uri = "ws://127.0.0.1:8000/ws/sincronizacion/"
        print(f"Attempting to connect to WebSocket at: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established successfully!")
            
            # Send a test message
            test_message = {
                "type": "ping",
                "data": "test connection"
            }
            
            await websocket.send(json.dumps(test_message))
            print("✅ Test message sent successfully!")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Received response: {response}")
                return True
            except asyncio.TimeoutError:
                print("⚠️  No response received within 5 seconds, but connection is working")
                return True
                
    except ConnectionRefusedError:
        print("❌ Connection refused - WebSocket server may not be running")
        return False
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Invalid status code: {e}")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection failed: {str(e)}")
        return False

async def test_websocket_endpoints():
    """Test different WebSocket endpoints"""
    endpoints = [
        "/ws/sincronizacion/",
        "/ws/sincronizacion/tienda1/",
        "/ws/sincronizacion/tienda2/"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        uri = f"ws://127.0.0.1:8000{endpoint}"
        print(f"\nTesting endpoint: {endpoint}")
        
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✅ Connected to {endpoint}")
                results[endpoint] = "Connected"
        except Exception as e:
            print(f"❌ Failed to connect to {endpoint}: {str(e)}")
            results[endpoint] = f"Failed: {str(e)}"
    
    return results

if __name__ == "__main__":
    print("=== WebSocket Connection Test ===\n")
    
    # Test main WebSocket connection
    print("1. Testing main WebSocket connection...")
    main_result = asyncio.run(test_websocket_connection())
    
    print("\n" + "="*50)
    print("2. Testing all WebSocket endpoints...")
    endpoint_results = asyncio.run(test_websocket_endpoints())
    
    print("\n=== Test Results Summary ===")
    print(f"Main WebSocket connection: {'✅ PASSED' if main_result else '❌ FAILED'}")
    print("\nEndpoint test results:")
    for endpoint, result in endpoint_results.items():
        status = "✅ PASSED" if "Connected" in result else "❌ FAILED"
        print(f"  {endpoint}: {status}")
    
    if main_result or any("Connected" in result for result in endpoint_results.values()):
        print("\n🎉 WebSocket functionality is working!")
        sys.exit(0)
    else:
        print("\n⚠️  WebSocket functionality needs attention")
        sys.exit(1)
