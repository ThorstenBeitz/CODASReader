import struct
import time
import numpy as np


class BinaryReader:

    field_names = ["S/R denom", "Intelligent Oversampling Factor", "Byte 4", "Byte 5", "Bytes in data file header", "Byte 8 - 11", 
        "Byte 12 - 15", "User annotation Bytes", "Height of graphics area", "Width of graphics area", "Cursor position (screen)", "Byte 24 - 27",
        "Time between samples", "Time file openened", "Time trailer written", "Waveform compression factor", "Byte 48 - 51", "Cursor position (file)",
        "time marker position (file)", "Left limit cursor", "Right limit cursor", "Byte 64", "Byte 65", "Byte 66", "Byte 67", "Byte 68 - 99", "Byte 100 - 101",
        "Byte 102 - 103", "Byte 104", "Byte 105", "Byte 106 - 107", "Byte 108", "Byte 109"]

    #takes one string argument for file location, returns TranslatedFile object
    @staticmethod
    def readFromFile(location):
        bin_data = open(location, "rb")
        #format strings for first 33 elements of header, all formats are standart size little endian
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

        #checking if the file is packed (stored in values[26][1])
        packed = False
        if int(values[26][1]) == 1:
            packed = True

        #number of acquired channels (stored in the last 5 (or 8) bits of values[0])
        if int(values[0][7]) == 0:
            acq_channels = int(values[0][-5:],2)
        else:
            acq_channels = int(values[0][-8:],2)

        #determining length of adc data in file which is dependent on whether file is packed or not
        #values[5] stores total number of bytes for adc storage
        #values[33] corresponds to first channel information, values[33][6] gives sample rate divider
        if packed:
            sample_sum = 0
            #calculate samples per channel and then sum them up over all channels
            for i in range(acq_channels):
                sample_sum = int(sample_sum + ((values[5] / acq_channels) - 1) / values[33 + i][6]) + 1
            adc_data_lim = int(2 * sample_sum) 
        else:
            adc_data_lim = int(values[5])

        #creating the adc data from the main body of the binary file
        adc_data = []
        for i in range(int(adc_data_lim / (2 * acq_channels))):
            #reading 2 bytes per data point per channel as unsigned short, then converting it into binary string
            adc_data_item = []
            for k in range(acq_channels):
                adc_data_bin = "{0:016b}".format(struct.unpack("<H", bin_data.read(2))[0])  
                #determining the sign of the binary number by looking for the for bit 0
                #then corectly converting the relevant bits back to decimal and adding them to item list
                #values[33] corresponds to first channel information, values[33][2] calibration scaling factor
                if int(adc_data_bin[0]) == 0:
                    adc_data_bin = int(adc_data_bin[1:14], 2) * values[33 + k][2]
                else:
                    #converting negative two's complement binary to decimal
                    adc_data_bin = (int(adc_data_bin[1:14], 2) - (1 << len(adc_data_bin[1:14]))) * values[33 + k][2]
                adc_data_item.append(adc_data_bin)
            #appending date and time to the item list, values[13] stores time of start of measurement,
            #values[12] stores time between measurements
            adc_data_item.append(time.strftime("%d %b %Y", time.gmtime(values[13] + i * values[12])))
            adc_data_item.append(time.strftime("%H:%M:%S", time.gmtime(values[13] + i * values[12])))
            #appending all values to adc_data list which will be stored
            adc_data.append(adc_data_item)

        #translating the trailer of the file
        trailer = []
        trailer_pointers = []
        trailer_item = []
        marker = True
        time_stamp = False
        #translating first part of trailer containing event marker pointers
        #values[6] stores total number of bytes in trailer part 1, each entry is a 4 byte long
        for i in range(int(values[6] / 4)):
            if marker:
                trailer_item = [struct.unpack("<l", bin_data.read(4))[0]]
                marker = False
                #determine whether or not nect long will be time and date stamp or not
                if trailer_item[-1] >= 0:
                    time_stamp = True
            elif time_stamp:
                trailer_item.append(struct.unpack("<l", bin_data.read(4))[0])
                time_stamp = False
            else:
                #determine whether next long is comment pointer or new marker pointer
                trailer_long = struct.unpack("<l", bin_data.read(4))[0]
                if trailer_long > -1 * values[5] / (2 * acq_channels):
                    trailer_pointers.append(trailer_item)
                    trailer_item = [trailer_long]
                    if trailer_item[-1] >= 0:
                        time_stamp = True
                else:
                    trailer_item.append(trailer_long)
                    trailer_pointers.append(trailer_item)
                    marker = True
        if len(trailer_pointers) == 0:
            trailer_pointers.append(trailer_item)
        elif trailer_pointers[-1] != trailer_item:
            trailer_pointers.append(trailer_item)
        trailer.append(trailer_pointers)
        
        #translating second part of trailer containing user annotations
        #values[7] stores number of user annotations
        trailer_annotations = []
        trailer_item = ""
        for i in range(values[7]):
            
            trailer_byte = struct.unpack("<b", bin_data.read(1))[0]
            if int(trailer_byte) == 0:
                trailer_annotations.append(trailer_item)
                trailer_item = ""
            else:
                trailer_item = trailer_item + chr(int(trailer_byte))
        trailer.append(trailer_annotations)

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

    #printing the trailer element of the file
    def printTrailer(self):
        print("Event marker pointers: ")
        for item in self.trailer[0]:
            print(item)
        print("User annotations")
        for i, item in enumerate(self.trailer[1]):
            print("Channel No. " + str(i) + " annotation: " + str(item))

    #print total length of header in bytes (stored in header[4])
    def printHeaderLength(self):
        print(self.header[4])

    #print total length of ADC data in bytes (stored in header[5])
    def printADCDataLength(self):
        print(self.header[5])

    #print time and date of start of data acquesition in GMT (stored in header[13]) 
    def printAcqTime(self):
        print(time.strftime("%d %b %Y , %H:%M:%S", time.gmtime(self.header[13])))

    #print number of acquired channels (stored in last 5 (or 8) bits in header[0])
    def printAcqChannels(self):
        if int(self.header[0][7]) == 0:
            print(int(self.header[0][-5:],2))
        else:
            print(int(self.header[0][-8:],2))  

    #print channel information for either one channel or a list of channel numbers, default is all channels
    def printChannelInfo(self, number = None):
        if number == None:
            number = list(range(0, int((self.header[4] - self.header[2] - 2) / self.header[3])))
        if type(number) == list:
            for item in number:
                print(self.header[33 + item])
        elif type(number) == int:
            print(self.header[33 + number])


location = "Desktop/BinaryReader/Files/20190923-T1.wdq"
trans_file = BinaryReader.readFromFile(location)
trans_file.printHeader()
trans_file.saveADCToFile("Desktop/BinaryReader/Files/output1.csv")
trans_file.printTrailer()
trans_file.printChannelInfo([1, 2])
trans_file.printAcqTime()