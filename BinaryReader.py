import struct
import time
import numpy as np


class BinaryReader:

    field_names = ["S/R denom", "Intelligent Oversampling Factor", "Byte 4", "Byte 5", "Bytes in data file header", "Byte 8 - 11", 
        "Byte 12 - 15", "User annotation Bytes", "Height of graphics area", "Width of graphics area", "Cursor position (screen)", "Byte 24 - 27",
        "Time between samples", "Time file openened", "Time trailer written", "Waveform compression factor", "Byte 48 - 51", "Cursor position (file)",
        "time marker position (file)", "Left limit cursor", "Right limit cursor", "Byte 64", "Byte 65", "Byte 66", "Byte 67", "Byte 68 - 99", "Byte 100 - 101",
        "Byte 102 - 103", "Byte 104", "Byte 105", "Byte 106 - 107", "Byte 108", "Byte 109"]

    @staticmethod
    def readFromFile(location):
        bin_data = open(location, "rb")
        #format strings for first 33 elements of header
        formats = ["<H", "<H", "<b", "<b", "<h", "<L", "<L", "<h", "<H", "<H", "<h", "<4b", "<d",
        "<l", "<l", "<l", "<l", "<l", "<l", "<h", "<h", "<b", "<b", "<b", "<b", "<32b", "<H", "<H", "<b", "<b", "<h", "<b", "<b"]
        #list that stores whether an element should be presented in binary or decimal (True = binary)
        bin_bool = [True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, True, True, False, True, False, True, True, True, True, True, True, True]
        values = []
        #format strings for the elements in the channel information
        channel_format = ["<f", "<f", "<d", "<d", "<6b", "<b", "<b", "<b", "<b", "<H"]
        #list that stores whether an element in the channel information should be presented in binary or decimal (True = binary)
        bin_bool_channel = [False, False, False, False, False, False, False, True, True, True]
        

        #reads and converts the first 33 elements of the file header 
        for i, form in enumerate(formats):
            values.append(struct.unpack(form, bin_data.read(struct.calcsize(form))))
            #reducing 1 element tuples to single element
            if len(values[-1]) == 1:
                values[-1] = values[-1][0]
            #converting all elements meant to be read bitwise to binary
            if bin_bool[i]:
                values[i] = ("{0:0" + str(struct.calcsize(form) * 8) + "b}").format(values[i])

        #reads and converts element 34 which contains channel information for all channels
        #values[4] stores total number of bytes in file header, values[3] stores number of bytes per channel,
        #values[2] stores start of channel information
        for i in range(int((values[4] - values[2] - 2)/values[3])):
            channel_values = []
            #creates the substructure of element 34
            for k, form in enumerate(channel_format):
                channel_values.append(struct.unpack(form, bin_data.read(struct.calcsize(form))))
                #reducing 1 element tuples to single element
                if len(channel_values[-1]) == 1:
                    channel_values[-1] = channel_values[-1][0]
                #converting all elements meant to be read bitwise to binary
                if bin_bool_channel[k]:
                    channel_values[k] = ("{0:0" + str(struct.calcsize(form) * 8) + "b}").format(channel_values[k])
            values.append(channel_values)

        #reading and converting last header element
        values.append(struct.unpack("<h", bin_data.read(struct.calcsize("<h")))[0])

        
        #creating the adc data from the main body of the binary file
        #values[5] stores total number of bytes for adc storage
        adc_data = []
        for i in range(int(values[5]/4)):
            #reading 4 bytes per data point as unsigned long, then converting it into binary string
            adc_data_bin = "{0:032b}".format(struct.unpack("<L", bin_data.read(4))[0])
            adc_data_item = []

            #determining the sign of each of the two elements in the long variable by looking for the for bit 0 and 16
            #then corectly converting the relevant bits back to decimal and adding them to item list
            if int(adc_data_bin[0]) == 0:
                adc_data_item.append(int(adc_data_bin[1:14], 2) * values[33][2])
            else:
                #converting negative two's complement binary to decimal
                adc_data_item.append((int(adc_data_bin[1:14], 2) - (1 << len(adc_data_bin[1:14]))) * values[33][2])
            if int(adc_data_bin[16]) == 0:
                adc_data_item.append(int(adc_data_bin[17:30], 2) * values[33][2])
            else:
                #converting negative two's complement binary to decimal
                adc_data_item.append((int(adc_data_bin[17:30], 2) - (1 << len(adc_data_bin[17:30]))) * values[33][2])

            #appending all values to adc_data list which will be stored
            adc_data.append([adc_data_item[0], adc_data_item[1], 
            time.strftime("%d %b %Y", time.gmtime(values[13] + i * values[12])),
            time.strftime("%H:%M:%S", time.gmtime(values[13] + i * values[12]))])

        trailer = []
        #returns a TranslatedFile object with the translated three main parts of the file as attributes
        return(TranslatedFile(values, adc_data, trailer))


class TranslatedFile:
    header = []
    adc_data = []
    trailer = []

    #creating a new translated file with lists for the header, adc_data and trailer of the file
    def __init__(self, header, adc_data, trailer):
        self.header = header
        self.adc_data = adc_data
        self.trailer = trailer

    #printing list with header values
    def printHeader(self):
        for i in range(len(self.header) - 1):
            if i < len(BinaryReader.field_names):
                print(BinaryReader.field_names[i] + ": " + str(self.header[i]))
            else:
                print("Channel No. " + str(i - len(BinaryReader.field_names)) + " information: " + str(self.header[i]))
        print("Fixed value of 8001H: " + str(self.header[-1]))

    #saves the adc data to a file with name 'name'
    def saveADCToFile(self, name, delim = ",", fmt = "%s"):
        np.savetxt(name, self.adc_data, delimiter = delim, fmt=fmt)

location = "Desktop/BinaryReader/Files/20190923-T1.wdq"
trans_file = BinaryReader.readFromFile(location)
trans_file.printHeader()
trans_file.saveADCToFile("Desktop/BinaryReader/Files/output1.csv")