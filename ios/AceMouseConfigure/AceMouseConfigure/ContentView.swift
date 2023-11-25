import SwiftUI
import CoreBluetooth

class BluetoothManager: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    var centralManager: CBCentralManager!
    @Published var isConnected = false
    @Published var calibrationInstructions = ""  // Moved here
    var aceMousePeripheral: CBPeripheral?  // Declare the peripheral property

    override init() {
           super.init()
           centralManager = CBCentralManager(delegate: self, queue: nil)
       }

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            centralManager.scanForPeripherals(withServices: [CBUUID(string: "UART_SERVICE_UUID")], options: nil)
        }
    }

    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String: Any], rssi RSSI: NSNumber) {
        if let deviceName = advertisementData[CBAdvertisementDataLocalNameKey] as? String {
            if deviceName == "AceMouse" {
                // Stop scanning for other devices to save power
                central.stopScan()

                // Save a reference to the peripheral
                self.aceMousePeripheral = peripheral  // Save the reference
                self.aceMousePeripheral?.delegate = self

                // Connect to the peripheral
                central.connect(peripheral, options: nil)
            }
        }
    }


    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        // Connection successful
        print("Connected to \(peripheral.name ?? "")")

        // Discover services here. You can pass nil to discover all services or pass an array of CBUUIDs if you're looking for specific services
        peripheral.discoverServices(nil)  // or peripheral.discoverServices([CBUUID(string: "YOUR_UART_SERVICE_UUID")])
    }
    
    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        if let error = error {
            print("Error receiving notification from characteristic: \(error.localizedDescription)")
            return
        }

        if let value = characteristic.value,
           let instruction = String(data: value, encoding: .utf8) {
            // Update the UI with the new instruction
            DispatchQueue.main.async {
                self.calibrationInstructions = instruction
            }
        }
    }
    
    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        if let error = error {
            print("Error discovering characteristics: \(error.localizedDescription)")
            return
        }

        guard let characteristics = service.characteristics else { return }

        for characteristic in characteristics {
            if characteristic.uuid == CBUUID(string: "INSTRUCTION_CHARACTERISTIC_UUID") {
                peripheral.setNotifyValue(true, for: characteristic)
            }
        }
    }
    
    func findCommandCharacteristic() -> CBCharacteristic? {
           guard let services = aceMousePeripheral?.services else {
               return nil
           }

           for service in services {
               for characteristic in service.characteristics ?? [] {
                   if characteristic.uuid == CBUUID(string: "COMMAND_CHARACTERISTIC_UUID") {
                       return characteristic
                   }
               }
           }

           return nil
       }


}



struct ContentView: View {
    @ObservedObject var bluetoothManager = BluetoothManager()
    
    var body: some View {
        NavigationView {
            VStack {
                if bluetoothManager.isConnected {
                    Text("Connected to AceMouse")
                        .foregroundColor(.green)
                    
                    if !bluetoothManager.calibrationInstructions.isEmpty {
                        Text("Instruction: \(bluetoothManager.calibrationInstructions)")
                    }

                    Button("Calibrate") {
                        startCalibration()
                    }
                } else {
                    Text("Searching for AceMouse...")
                        .foregroundColor(.orange)
                }
            }
            .navigationBarTitle("AceMouse Calibration")
        }
    }

    private func startCalibration() {
        guard let peripheral = bluetoothManager.aceMousePeripheral,
              let commandCharacteristic = bluetoothManager.findCommandCharacteristic() else {
            print("Peripheral or characteristic not found")
            return
        }

        let calibrationCommand = "Start Calibration"
        if let data = calibrationCommand.data(using: .utf8) {
            peripheral.writeValue(data, for: commandCharacteristic, type: .withResponse)
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
