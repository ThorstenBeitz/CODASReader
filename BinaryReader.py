import struct

class BinaryReader:
        
    @staticmethod
    def printHeader(location):
        bin_data = open(location, "rb")
        formats = ["H", "H", "b", "b", "h", "L", "L", "h", "H", "H", "h", "4b", "d",
        "l", "l", "l", "l", "l", "l", "h", "h", "b", "b", "b", "b", "32b", "H", "H", "b", "b", "h", "b", "b"]
        values = []
        channel_format = ["f", "f", "d", "d", "6b", "b", "b", "b", "b", "H"]
        field_names = ["S/R denom", "Intelligent Oversampling Factor", "Byte 4", "Byte 5", "Bytes in data file header", "Byte 8 - 11", 
        "Byte 12 - 15", "User annotation Bytes", "Height of graphics area", "Width of graphics area", "Cursor position", "Byte 24 - 27",
        "Time between samples", "Time file openened", "Time trailer written", "Waveform compression factor", "Byte 48 - 51", "Byte 52 - 55",
        "Byte 56 - 59", "Left limit cursor", "Right limit cursor", "Byte 64", "Byte 65", "Byte 66", "Byte 67", "Byte 68 - 99", "Byte 100 - 101",
        "Byte 102 - 103", "Byte 104", "Byte 105", "Byte 106 - 107", "Byte 108", "Byte 109"]

        for form in formats:
            values.append(struct.unpack(form, bin_data.read(struct.calcsize(form))))
            if len(values[-1]) == 1:
                values[-1] = values[-1][0]


        for i in range(int((values[4] - 112)/values[3])):
            channel_values = []
            for form in channel_format:
                channel_values.append(struct.unpack(form, bin_data.read(struct.calcsize(form))))
                if len(channel_values[-1]) == 1:
                    channel_values[-1] = channel_values[-1][0]
            values.append(channel_values)
            #i = i + bytes_per_channel

        values.append(struct.unpack("h", bin_data.read(struct.calcsize("h")))[0])

        for i in range(len(values) - 1):
            if i < len(field_names):
                print(field_names[i] + ": " + str(values[i]))
            else:
                print("Channel No. " + str(i - len(field_names)) + " information: " + str(values[i]))
        print("Fixed value of 8001H: " + str(values[-1]))


location = "Desktop/BinaryReader/Files/20190923-T1.wdq"
BinaryReader.printHeader(location)
