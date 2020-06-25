import struct
import time
import numpy as np


class CODASReader:
    """Object to read, translate, store and write content from
    CODAS files. \n
    Information on the file format can be found at \n
    https://www.dataq.com/resources/techinfo/ff.htm"""

    bytes_in_file = 0
    header = []
    adc_data = []
    trailer = []
    packed = False
    hiRes = False
    acq_channels = 0
    adc_data_bytes = 0

    def __init__(self, location, read_header=True):
        bin_data = open(location, "rb")
        bin_data.seek(0, 2)
        self.bytes_in_file = bin_data.tell()
        bin_data.seek(0, 0)
        bin_data.close()
        if read_header:
            self.readHeader()

    def readHeader(self):
        bin_data = open(location, "rb")
        bin_data.seek(0, 0)

        # format strings for first 33 elements of header,
        # all formats are standart size little endian
        formats = ["<H", "<H", "<b", "<b", "<h", "<L", "<L", "<h", "<H",
                   "<H", "<h", "<4b", "<d", "<l", "<l", "<l", "<l",
                   "<l", "<l", "<h", "<h", "<b", "<b", "<b", "<b",
                   "<32b", "<H", "<H", "<b", "<b", "<h", "<b", "<b"]

        # list that stores whether an element should be presented
        # in binary or decimal (True = binary)
        bin_bool = [True, True, False, False, False, False, False, False,
                    False, False, False, False, False, False, False, False,
                    False, False, False, False, False, True, True, False,
                    True, False, True, True, True, True, True, True, True]
        self.header = []
        # format strings for the elements in the channel information
        channel_format = ["<f", "<f", "<d", "<d",
                          "<6b", "<b", "<b", "<b", "<b", "<H"]
        # list that stores whether an element in the channel information
        # should be presented in binary or decimal (True = binary)
        bin_bool_channel = [False, False, False, False,
                            False, False, False, True, True, True]

        # reads and converts the first 33 elements of the file header
        for i, form in enumerate(formats):
            self.header.append(struct.unpack(
                form, bin_data.read(struct.calcsize(form))))
            # reducing 1 element tuples to single element
            if len(self.header[-1]) == 1:
                self.header[-1] = self.header[-1][0]
            # converting all elements meant to be read bitwise to binary
            if bin_bool[i]:
                self.header[i] = (
                    "{0:0" + str(struct.calcsize(form) * 8)
                    + "b}").format(self.header[i])

        # reads and converts element 34 which contains
        # channel information for all channels
        # header[4] stores total number of bytes in file header,
        # header[3] stores number of bytes per channel,
        # header[2] stores start of channel information
        for i in range(int((self.header[4] - self.header[2] - 2)
                           / self.header[3])):
            channel_info = []
            # creates the substructure of element 34
            for k, form in enumerate(channel_format):
                channel_info.append(struct.unpack(
                    form, bin_data.read(struct.calcsize(form))))
                # reducing 1 element tuples to single element
                if len(channel_info[-1]) == 1:
                    channel_info[-1] = channel_info[-1][0]
                # converting all elements meant to be read
                # bitwise to binary
                if bin_bool_channel[k]:
                    channel_info[k] = (
                        "{0:0" + str(struct.calcsize(form) * 8)
                        + "b}").format(channel_info[k])
            self.header.append(channel_info)

        # reading and converting last header element
        self.header.append(struct.unpack(
            "<h", bin_data.read(struct.calcsize("<h")))[0])
        # checking if the file is packed (stored in self.header[26][1])
        if int(self.header[26][1]) == 1:
            self.packed = True

        # number of acquired channels
        # (stored in the last 5 (or 8) bits of self.header[0])
        if int(self.header[0][7]) == 0:
            self.acq_channels = int(self.header[0][-5:], 2)
        else:
            self.acq_channels = int(self.header[0][-8:], 2)

        # determining length of adc data in file
        # which is dependent on whether file is packed or not
        # self.header[5] stores total number of bytes for adc storage
        # self.header[33] corresponds to first channel information,
        # self.header[33][6] gives sample rate divider
        if self.packed:
            sample_sum = 0
            # calculate samples per channel
            # and then sum them up over all channels
            for i in range(self.acq_channels):
                sample_sum = int(
                    sample_sum + ((self.header[5] / self.acq_channels) - 1)
                    / self.header[33 + i][6]) + 1
            self.adc_data_bytes = int(2 * sample_sum)
        else:
            self.adc_data_bytes = int(self.header[5])

        # determining whether file is hiRes and uses 16 bit data
        # (stored in bit 14 of self.header[26])
        if int(self.header[26][14]) == 1:
            self.hiRes = True

        bin_data.close

    def readADC(self):
        bin_data = open(location, "rb")
        bin_data.seek(self.header[4], 0)
        if self.hiRes:
            adc_bit_length = 16
        else:
            adc_bit_length = 14

        # creating the adc data from the main body of the binary file
        self.adc_data = []
        for i in range(int(self.adc_data_bytes / (2 * self.acq_channels))):
            # reading 2 bytes per data point per channel
            # as unsigned short, then converting it into binary string
            adc_data_item = []
            for k in range(self.acq_channels):
                adc_data_bin = "{0:016b}".format(
                    struct.unpack("<H", bin_data.read(2))[0])
                # determining the sign of the binary number
                # by looking for bit 0,
                # then corectly converting the relevant bits back
                # to decimal and adding them to item list
                # self.header[33] corresponds to first channel info,
                # self.header[33][2] calibration scaling factor
                if int(adc_data_bin[0]) == 0:
                    adc_data_bin = (int(adc_data_bin[1:adc_bit_length], 2)
                                    * self.header[33 + k][2])
                else:
                    # converting negative two's complement binary
                    # to decimal
                    adc_data_bin = ((int(adc_data_bin[1:adc_bit_length], 2)
                                     - (1 << len(adc_data_bin[1:adc_bit_length]
                                                 ))) * self.header[33 + k][2])
                adc_data_item.append(adc_data_bin)
            # appending date and time to the item list,
            # self.header[13] stores time of start of measurement,
            # self.header[12] stores time between measurements
            adc_data_item.append(time.strftime(
                "%d %b %Y", time.gmtime(self.header[13] + i * self.header[12])))
            adc_data_item.append(time.strftime(
                "%H:%M:%S", time.gmtime(self.header[13] + i * self.header[12])))
            # appending all values to adc_data list which will be stored
            self.adc_data.append(adc_data_item)

        bin_data.close()

    def readTrailer(self):

        bin_data = open(location, "rb")
        bin_data.seek(self.header[4] + self.adc_data_bytes, 0)
        # translating the trailer of the file
        self.trailer = []
        trailer_pointers = []
        trailer_item = []
        marker = True
        time_stamp = False

        if self.hiRes:
            channels_hiRes = 1
        else:
            channels_hiRes = self.acq_channels
        # translating first part of trailer containing
        # event marker pointers
        # self.header[6] stores total number of bytes in trailer part 1,
        # each entry is a 4 byte long
        for i in range(int(self.header[6] / 4)):
            if marker:
                trailer_item = [struct.unpack("<l", bin_data.read(4))[0]]
                marker = False
                # determine whether or not next long will be
                # time and date stamp or not
                if trailer_item[-1] >= 0:
                    time_stamp = True
            elif time_stamp:
                trailer_item.append(struct.unpack("<l", bin_data.read(4))[0])
                time_stamp = False
            else:
                # determine whether next long is comment pointer
                # or new marker pointer
                trailer_long = struct.unpack("<l", bin_data.read(4))[0]
                if trailer_long > -1 * self.header[5] / (2 * channels_hiRes):
                    trailer_pointers.append(trailer_item)
                    trailer_item = [trailer_long]
                    if trailer_item[-1] >= 0:
                        time_stamp = True
                else:
                    trailer_item.append(trailer_long)
                    trailer_pointers.append(trailer_item)
                    marker = True
        # add last item to list if has not been added
        # which happens if the last item has no comment pointer
        if len(trailer_pointers) == 0:
            trailer_pointers.append(trailer_item)
        elif trailer_pointers[-1] != trailer_item:
            trailer_pointers.append(trailer_item)
        self.trailer.append(trailer_pointers)

        # translating second part of trailer
        # containing user annotations,
        # null character (0) ends each annotation
        # self.header[7] stores number of user annotations
        trailer_annotations = []
        trailer_item = ""
        for i in range(self.header[7]):

            trailer_byte = struct.unpack("<b", bin_data.read(1))[0]
            if int(trailer_byte) == 0:
                trailer_annotations.append(trailer_item)
                trailer_item = ""
            else:
                trailer_item = trailer_item + chr(int(trailer_byte))
        self.trailer.append(trailer_annotations)

        # translating all remaining bytes as
        # event marker comment part of the trailer,
        # code works similiarly to user annotation above
        trailer_item = ""
        trailer_comments_list = []
        # trailer_comments = bin_data.read()
        for i in range(self.bytes_in_file - (self.header[4]
                                             + self.adc_data_bytes
                                             + self.header[6]
                                             + self.header[7])):
            trailer_byte = struct.unpack("<b", bin_data.read(1))[0]
            if int(trailer_byte) == 0:
                trailer_comments_list.append(trailer_item)
                trailer_item = ""
            else:
                trailer_item = trailer_item + chr(int(trailer_byte))
        self.trailer.append(trailer_comments_list)

        bin_data.close()

    # printing list with header values
    def printHeader(self):
        """Prints header of the file"""

        field_names = ["S/R denom", "Intelligent Oversampling Factor",
                       "Byte 4", "Byte 5", "Bytes in data file header",
                       "Byte 8 - 11", "Byte 12 - 15", "User annotation Bytes",
                       "Height of graphics area", "Width of graphics area",
                       "Cursor position (screen)", "Byte 24 - 27",
                       "Time between samples", "Time file openened",
                       "Time trailer written", "Waveform compression factor",
                       "Byte 48 - 51", "Cursor position (file)",
                       "time marker position (file)", "Left limit cursor",
                       "Right limit cursor", "Byte 64", "Byte 65", "Byte 66",
                       "Byte 67", "Byte 68 - 99", "Byte 100 - 101",
                       "Byte 102 - 103", "Byte 104", "Byte 105",
                       "Byte 106 - 107", "Byte 108", "Byte 109"]

        for i in range(len(self.header) - 1):
            if i < len(field_names):
                print(field_names[i] + ": " + str(self.header[i]))
            else:
                print("Channel No. " + str(i - len(field_names))
                      + " information: "
                      + str(self.header[i]))
        print("Fixed value of 8001H: " + str(self.header[-1]))

    # saves the adc data to a file with name 'name'
    def saveADCsToCSV(self, name, delim=",", fmt="%s"):
        """param name : str \n
        param delim : str, optional \n
        param fmt : str, optional \n
        Saves the ADC data of the file to a CSV file of name 'name'."""
        # np.savetxt(name, self.adc_data, delimiter = delim, fmt=fmt)
        with open(name, "w", newline="\n") as file:
            for item in self.adc_data:
                for seg in item:
                    file.write(str(seg))
                    file.write(delim)
                file.write("\n")

    # printing the trailer element of the file
    def printTrailer(self):
        """Prints the trailer of the file"""
        print("Event marker pointers: ")
        for item in self.trailer[0]:
            print(item)
        print("User annotations")
        for i, item in enumerate(self.trailer[1]):
            print("Channel No. " + str(i) + " annotation: " + str(item))
        print("Event marker comments: ")
        for item in self.trailer[2]:
            print(item)

    # print total length of header in bytes (stored in header[4])
    def printHeaderLength(self):
        """Prints total length of header in the file in bytes"""
        print(self.header[4])

    # print total length of ADC data in bytes (stored in header[5])
    def printADCDataLength(self):
        """Prints total length of ADC data in the file in bytes"""
        print(self.header[5])

    # print time and date of start of data acquesition in GMT
    # (stored in header[13])
    def printAcqTime(self):
        """Prints time and date of start of data acquesition"""
        print(time.strftime("%d %b %Y , %H:%M:%S",
                            time.gmtime(self.header[13])))

    # print number of acquired channels
    # (stored in last 5 (or 8) bits in header[0])
    def printAcqChannels(self):
        """Prints number of acquired channels"""
        print(self.acq_channels)

    # print channel information for either one channel
    # or a list of channel numbers, default is all channels
    def printChannelInfo(self, number=None):
        """param number : int or list of int \n
        Prints the channel information stored in the header
        for the channel(s) given. \n
        The default is to print all channels"""
        if number == None:
            number = list(
                range(0, int((self.header[4] - self.header[2] - 2)
                             / self.header[3])))
        if type(number) == list:
            for item in number:
                print(self.header[33 + item])
        elif type(number) == int:
            print(self.header[33 + number])


location = "Desktop/BinaryReader/Files/20190923-T1.wdq"

codas_reader = CODASReader(location)
codas_reader.readADC()
codas_reader.readTrailer()
codas_reader.saveADCsToCSV("Desktop/BinaryReader/Files/output1.csv")
codas_reader.printHeader()
codas_reader.printTrailer()
codas_reader.printAcqChannels()
