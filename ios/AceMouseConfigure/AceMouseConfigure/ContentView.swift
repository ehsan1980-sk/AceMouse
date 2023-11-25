import SwiftUI
import CoreBluetooth

class BluetoothManager: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    var centralManager: CBCentralManager!
    @Published var isConnected = false
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
        // Connection successful, discover services
    }

    // Add other delegate methods to handle discovery, data transfer, etc.
}

struct ContentView: View {
    @State private var isConnected = false
    @State private var calibrationInstructions = ""
    @ObservedObject var bluetoothManager = BluetoothManager()
    
    var body: some View {
        NavigationView {
            VStack {
                if isConnected {
                    Text("Connected to AceMouse")
                        .foregroundColor(.green)
                    
                    if !calibrationInstructions.isEmpty {
                        Text("Instruction: \(calibrationInstructions)")
                    }

                    Button("Calibrate") {
                        // Trigger calibration process
                        startCalibration()
                    }
                } else {
                    Text("Searching for AceMouse...")
                        .foregroundColor(.orange)
                    // Add logic to search for AceMouse
                }
            }
            .navigationBarTitle("AceMouse Calibration")
        }
        .onAppear {
            // Add logic to start scanning for devices
        }
    }

    private func startCalibration() {
        // Add logic to send calibration command
        // Update `calibrationInstructions` based on responses
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
