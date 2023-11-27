# AceMouse
 Wireless mouse in the smallest package with all the bells and whistles you would ever want. And open source

## Aims

- A VERY Small wireless mouse
- VERY Battery efficient
- Can be used on a head/hand/knee. Ie the IMU may change in position so a user needs to tell the system which way is top/forward etc
- Deal with sensitive movement and grosser movement. So filter out jerks etc if needed.
- DONT WORRY ABOUT CLICKS :)
- Allow for proportional control as an option. I.e the longer you hold in a direction the faster it goes


## Notes

- A very small nrf52840 and IMU - im looking at the lsm6ds3 as its built into the seeed studio nrf52840 sense
- We want to use it as a mouse. So it takes the acceleration and gyro data. Converts this to mouse ble hid movements. I have it working in circuitPython but we need to add some functionality. 
- Notably: - Add proportional movement. So longer you hold it in one direction it stays there
- Add in option to reposition forward. I have started some code around calibrating direction of the IMU but i dont think we need it. This code seems to suggest we can just figure out which way is top. We just need a paramter to be provided from the user saying which was is forward. https://forum.seeedstudio.com/t/xiao-nrf52840-sense-imu-parked-demo-with-sleep-interrupt-button/272954
- Have an option for sensitivity. I tried doing this in circuitPython but my logic is bad
- Use sleep modes for better battery consumption. This looks really fiddly and tricky in circuitpython and is the main reason we need to consider going to arduino C code.. (alarms in circuitpython - and accessing the IMU interrupt data is spinning my head). Its a shame - i do like the idea of mounting the circuitpy drive and just editing a json file. We could use BLEUART and app (see my xcode file which starts this with a calibration thing.. we could just make this somekind of editor to BLEUART remote calls if we need to but we would need a way of turning this mode on and off so we dont waste power)


## Hardware

- Aim of this is to do this with as minimal electronics as possible.
- We use currently a seeed studio XIAO nrf52840 Sense. This has a 6 axis IMU - and bluetooth stack is solid.
- You could easily seperate this out to just the IMU and a seperate chip.

## Software

- CircuitPython on the board
- SwiftUI app to configure over bleuart


