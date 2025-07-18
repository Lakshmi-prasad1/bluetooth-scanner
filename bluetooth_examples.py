# examples/basic_scan.py
"""
Basic Bluetooth scanning example
Simple demonstration of device discovery
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bluetooth_scanner import BluetoothScanner

def main():
    print("=== Basic Bluetooth Scan Example ===")
    
    # Create scanner with 15-second duration
    scanner = BluetoothScanner(scan_duration=15, lookup_names=True)
    
    # Perform scan
    scanner.scan_classic_bluetooth()
    
    # Display results
    scanner.display_statistics()
    
    # Save results
    scanner.save_results("basic_scan_results.json")

if __name__ == "__main__":
    main()

# examples/service_monitor.py
"""
Service monitoring example
Demonstrates continuous service discovery
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bluetooth_scanner import BluetoothScanner

def main():
    print("=== Service Monitor Example ===")
    
    scanner = BluetoothScanner(scan_duration=10, lookup_names=True)
    
    # First, discover devices
    print("Step 1: Discovering devices...")
    scanner.scan_classic_bluetooth()
    
    # Then monitor services for discovered devices
    print("\nStep 2: Monitoring services...")
    
    for address in scanner.discovered_devices:
        print(f"\n--- Services for {address} ---")
        scanner.scan_for_services(address)
        time.sleep(2)  # Brief pause between service scans

if __name__ == "__main__":
    main()

# tests/test_scanner.py
"""
Unit tests for Bluetooth Scanner
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bluetooth_scanner import BluetoothScanner

class TestBluetoothScanner(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.scanner = BluetoothScanner(scan_duration=5, lookup_names=True)
    
    def test_scanner_initialization(self):
        """Test scanner initialization"""
        self.assertEqual(self.scanner.scan_duration, 5)
        self.assertTrue(self.scanner.lookup_names)
        self.assertEqual(len(self.scanner.discovered_devices), 0)
        self.assertFalse(self.scanner.scanning)
    
    def test_decode_device_class(self):
        """Test device class decoding"""
        # Test known device classes
        self.assertEqual(self.scanner.decode_device_class(0x0100), "Computer")
        self.assertEqual(self.scanner.decode_device_class(0x0200), "Phone")
        self.assertEqual(self.scanner.decode_device_class(0x0400), "Audio/Video")
        self.assertEqual(self.scanner.decode_device_class(None), "Unknown")
    
    @patch('bluetooth.discover_devices')
    def test_scan_classic_bluetooth_no_devices(self, mock_discover):
        """Test scanning when no devices are found"""
        mock_discover.return_value = []
        
        # Capture output
        with patch('builtins.print') as mock_print:
            self.scanner.scan_classic_bluetooth()
            
        # Verify no devices message was printed
        mock_print.assert_any_call("❌ No Classic Bluetooth devices found")
    
    @patch('bluetooth.discover_devices')
    @patch('bluetooth.lookup_device_class')
    @patch('bluetooth.find_service')
    def test_scan_classic_bluetooth_with_devices(self, mock_find_service, 
                                                mock_lookup_class, mock_discover):
        """Test scanning with discovered devices"""
        # Mock device discovery
        mock_discover.return_value = [("AA:BB:CC:DD:EE:FF", "Test Device")]
        mock_lookup_class.return_value = 0x0100  # Computer class
        mock_find_service.return_value = [{"name": "Test Service"}]
        
        self.scanner.scan_classic_bluetooth()
        
        # Verify device was stored
        self.assertEqual(len(self.scanner.discovered_devices), 1)
        self.assertIn("AA:BB:CC:DD:EE:FF", self.scanner.discovered_devices)
        
        device = self.scanner.discovered_devices["AA:BB:CC:DD:EE:FF"]
        self.assertEqual(device["name"], "Test Device")
        self.assertEqual(device["address"], "AA:BB:CC:DD:EE:FF")
        self.assertEqual(device["type"], "Classic")
    
    @patch('bluetooth.BluetoothError')
    @patch('bluetooth.discover_devices')
    def test_scan_bluetooth_error_handling(self, mock_discover, mock_error):
        """Test error handling during scanning"""
        mock_discover.side_effect = Exception("Bluetooth not available")
        
        with patch('builtins.print') as mock_print:
            self.scanner.scan_classic_bluetooth()
            
        # Verify error message was printed
        mock_print.assert_any_call("❌ Error during scanning: Bluetooth not available")
    
    def test_get_device_info_exception_handling(self):
        """Test device info retrieval with exceptions"""
        with patch('bluetooth.lookup_device_class', side_effect=Exception("Error")):
            with patch('bluetooth.find_service', side_effect=Exception("Error")):
                info = self.scanner.get_device_info("AA:BB:CC:DD:EE:FF")
                
                self.assertEqual(info['class'], 'Unknown')
                self.assertEqual(info['services'], [])
    
    def test_save_results(self):
        """Test saving results to JSON file"""
        # Add test data
        self.scanner.discovered_devices = {
            "AA:BB:CC:DD:EE:FF": {
                "name": "Test Device",
                "address": "AA:BB:CC:DD:EE:FF",
                "type": "Classic"
            }
        }
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('json.dump') as mock_dump:
                self.scanner.save_results("test.json")
                
                mock_open.assert_called_once_with("test.json", 'w')
                mock_dump.assert_called_once()
    
    def test_display_statistics_no_devices(self):
        """Test statistics display with no devices"""
        with patch('builtins.print') as mock_print:
            self.scanner.display_statistics()
            
        mock_print.assert_any_call("📊 No devices discovered yet")
    
    def test_display_statistics_with_devices(self):
        """Test statistics display with devices"""
        # Add test data
        self.scanner.discovered_devices = {
            "AA:BB:CC:DD:EE:FF": {"type": "Classic"},
            "11:22:33:44:55:66": {"type": "BLE"}
        }
        
        with patch('builtins.print') as mock_print:
            self.scanner.display_statistics()
            
        mock_print.assert_any_call("Total devices discovered: 2")

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_device_class_edge_cases(self):
        """Test device class decoding edge cases"""
        scanner = BluetoothScanner()
        
        # Test with None
        self.assertEqual(scanner.decode_device_class(None), "Unknown")
        
        # Test with invalid class
        result = scanner.decode_device_class(0xFFFF)
        self.assertIn("Unknown", result)
        
        # Test with zero
        self.assertEqual(scanner.decode_device_class(0x0000), "Miscellaneous")

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

# tests/test_integration.py
"""
Integration tests for Bluetooth Scanner
These tests require actual Bluetooth hardware
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bluetooth_scanner import BluetoothScanner

class TestIntegration(unittest.TestCase):
    """Integration tests that require Bluetooth hardware"""
    
    @unittest.skipUnless(os.environ.get('BLUETOOTH_TESTS'), 
                        "Set BLUETOOTH_TESTS=1 to run hardware tests")
    def test_real_bluetooth_scan(self):
        """Test actual Bluetooth scanning (requires hardware)"""
        scanner = BluetoothScanner(scan_duration=5, lookup_names=False)
        
        try:
            scanner.scan_classic_bluetooth()
            # Test passes if no exception