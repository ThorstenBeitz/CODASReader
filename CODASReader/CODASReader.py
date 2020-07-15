import struct
import time
import numpy as np


class CODASReader:
    """Object to read, translate, store and write content from
    CODAS files. \n
    Information on the file format can be found at \n
    https://www.dataq.com/resources/techinfo/ff.htm \n
    The file header is read automatically by default upon creation
    of this object. \n
    It is recommended not to change this as the header must be read
    before any other part of the file can be processed."""

    location = ""
    bytes_in_file = 0
    channels = []
    header = []
    adc_data = []
    adc_time_stamps = []
    adc_scaling = []
    trailer = []
    packed = False
    hiRes = False
    acq_channels = 0
    adc_data_bytes = 0

    def __init__(self, location, read_header=True):
        self.location = location
        bin_data = open(self.location, "rb")
        # determining total length of file in bytes
        bin_data.seek(0, 2)
        self.bytes_in_file = bin_data.tell()
        bin_data.seek(0, 0)
        bin_data.close()
        if read_header:
            self.readHeader()

    # reads header of the file. This is done automatically when creating
    # a new CODASReader object by default.
    # must be run before reading the rest of the file.
    def readHeader(self):
        """Reads the header of the file. \n
        This is done automatically by default when creating a new
        CODASReader object. \n
        The header must be read before any other part of the file can
        be read."""
        bin_data = open(self.location, "rb")
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
            "<H", bin_data.read(struct.calcsize("<H")))[0])
        # if control byte of header does not match the expected value
        # raise an error and the recorded control byte
        if self.header[-1] != 32769:
            raise(ValueError("File may be truncated or corrupted: "
                             + "Header control byte "
                             + "does not match expected value of 32769: "
                             + str(self.header[-1]) + "\n"))
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

    # reads ADC data from file.
    # takes a list of channel or a single channel number as optional
    # argument so it only reads the data for those channels.
    # takes start time and end time (in s since start) as optional
    # arguments to only read data within a certain time frame,
    # the default is to read from start of data acquesition to finish.
    # save_memory determines whether the scaling factor will be applied
    # to all values and saved or whether it is simply stored once to
    # then manually be applied later
    def readADC(self, channels=None, start_time=0, end_time=None,
                save_memory=True, az_time=True):
        """PARAMETERS: \n
        channels : int or array-like of int, optional \n
            Must be able to be converted into a numpy array. \n
            A list of all channels from which data should be read. \n
            The first channel has index 0. \n
            Default is reading all acquired channels. \n
            Use 'printAcqChannels' to see number the number of
            acquired channels. \n
        start_time : float, optional \n
            Time in seconds since start of data acquesition at which
            the first ADC data should be read. \n
            Default is 0 \n
        end_time : float, optional \n
            Time in seconds since start of data acquesition at which
            the last ADC data should be read. \n
            Default is until end of ADC data section in file. \n
        save_memory : bool, optional \n
            Decides whether the scaling factor is applied to the data
            or if the scaling factor is saved in a separate array \n
            before it is saved to the array \n
            If true, the data will be saved as int16, which is the
            way it is natively stored in the file
            (no loss of information) \n
            If false, the data is stored as float. \n
            Default is True \n
            It is recommended to use save_memory = True for large files
            and / or for systems with limited ram. \n
        az_time: bool, optional \n
            Decides whether the time stamps are in UTC or in
            Arizona local time (VERITAS telescope location) \n
            Default is True (Arizona time) \n
        \n Use 'printAcqTime' and 'printFinishTime' to get start and
        finish time of the data acquesition respectively
        \n The header of the file must be read before
        reading the ADC data.
        \n This method reads the ADC data from the file and saves the
        translated data to the adc_data array in this object. """
        # raise error if header list is empty
        if len(self.header) == 0:
            raise RuntimeError("Header has not been read or is empty"
                               + "Use 'readHeader' to read header")
        # converting channels argument into numpy array to loop over
        if channels == None:
            channels = np.arange(self.acq_channels)
        elif type(channels) == int:
            channels = np.array([channels])
        else:
            channels = np.array(channels)
        # determining how many bits are used to store the data,
        # which depends on whether the file is hiRes or not
        if self.hiRes:
            adc_bit_length = 16
        else:
            adc_bit_length = 14
        # opening file
        bin_data = open(self.location, "rb")
        # determining start byte based on the start time given
        # self.header[12] stores time bewteen samples,
        # self.header[4] stores number of bytes in header
        # each channel takes up 2 bytes per datapoint in adc data
        start_byte = int((start_time / self.header[12]) * self.acq_channels * 2
                         + self.header[4])
        bin_data.seek(start_byte, 0)
        # determining end byte relative to the start byte based on
        # end time given, if none is given all adc data from start
        # byte to the end of the adc data section is read
        if end_time == None:
            end_byte = self.adc_data_bytes + self.header[4] - start_byte
        else:
            end_byte = int(((end_time - start_time) / self.header[12])
                           * self.acq_channels * 2)

        # setting up adc data array based on whether save_memory is
        # set to true or not
        if save_memory:
            self.adc_data = np.empty([int(end_byte / (2 * self.acq_channels)),
                                      len(channels)], dtype=np.int16)
        else:
            self.adc_data = np.empty([int(end_byte / (2 * self.acq_channels)),
                                      len(channels)])
        # applying a 7 hour offset if az_time is True to account for
        # the 7 hour difference between arizona time and UTC
        if az_time:
            offset = -3600 * 7
        else:
            offset = 0
        # setting up arrays to store the time stamps and the scaling
        # factor for each channel.
        # these are stored separately to increase memory efficiency on
        # the main data
        self.adc_time_stamps = np.empty([int(end_byte / (2 * self.acq_channels)),
                                         3], dtype="U20")
        self.adc_scaling = np.empty(len(channels))
        # creating the adc data from the main body of the binary file
        for i in range(int(end_byte / (2 * self.acq_channels))):
            # reading 2 bytes per data point per channel
            # as unsigned short, then converting it into binary string
            for k, channel in enumerate(channels):
                if channel >= self.acq_channels:
                    raise IndexError("One or more of the provided channel "
                                     + "numbers "
                                     + "are outside the range of channels "
                                     + "with recorded data: \n"
                                     + str(channel))
                # finding byte in adc data section where the current
                # channel's information for the current time is stored
                bin_data.seek(start_byte + 2 * i * self.acq_channels + 2
                              * channel, 0)
                adc_data_bin = "{0:016b}".format(
                    struct.unpack("<H", bin_data.read(2))[0])
                # determining the sign of the binary number
                # by looking for bit 0,
                # then corectly converting the relevant bits back
                # to decimal and adding them to item list
                if int(adc_data_bin[0]) == 0:
                    adc_data_bin = (int(adc_data_bin[1:adc_bit_length], 2))
                else:
                    # converting negative two's complement binary
                    # to decimal
                    adc_data_bin = ((int(adc_data_bin[1:adc_bit_length], 2)
                                     - (1 << len(adc_data_bin[1:adc_bit_length]
                                                 ))))
                # scaling factor is only applied if save_memory is set
                # to false
                if not save_memory:
                    adc_data_bin = adc_data_bin * self.header[33 + channel][2]
                self.adc_data[i, k] = adc_data_bin
            # appending date and time to the item list,
            # self.header[13] stores time of start of measurement,
            # self.header[12] stores time between measurements
            self.adc_time_stamps[i, 0] = (time.strftime(
                "%m-%d-%Y", time.gmtime(self.header[13] + start_time + i
                                        * self.header[12] + offset)))
            self.adc_time_stamps[i, 1] = (time.strftime(
                "%H:%M:%S", time.gmtime(self.header[13] + start_time + i
                                        * self.header[12] + offset)))
            self.adc_time_stamps[i, 2] = "{:.4f}".format(i * self.header[12])
        # if save_memory is set to true, scaling factors will be saved
        # in a separate list
        if save_memory:
            for i, channel in enumerate(channels):
                self.adc_scaling[i] = (self.header[33 + channel][2])
        # saving channels numbers
        self.channels = channels

        bin_data.close()

    # reads trailer of the file
    # header must be read first
    def readTrailer(self):
        """Reads the trailer of the file. \n
        The header of the file must be read before
        reading the trailer."""
        # raise error if header list is empty
        if len(self.header) == 0:
            raise RuntimeError("Header has not been read or is empty"
                               + "Use 'readHeader' to read header")
        bin_data = open(self.location, "rb")
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
                trailer_item[-1] = (np.abs(trailer_item[-1]) * 2
                                    * channels_hiRes) + self.header[4]
                trailer_item[-1] = (int((trailer_item[-1] - self.header[4])
                                        / (2 * self.acq_channels))
                                    * self.header[12])
                marker = False
                # determine whether or not next long will be
                # time and date stamp or not
                if trailer_item[-1] >= 0:
                    time_stamp = True
            elif time_stamp:
                trailer_item.append(struct.unpack("<l", bin_data.read(4))[0])
                trailer_item[-1] = trailer_item[-1] + self.header[13]
                time_stamp = False
            else:
                # determine whether next long is comment pointer
                # or new marker pointer
                trailer_long = struct.unpack("<l", bin_data.read(4))[0]
                if trailer_long > -1 * self.header[5] / (2 * channels_hiRes):
                    trailer_pointers.append(trailer_item)
                    trailer_long = (np.abs(trailer_long) * 2
                                    * channels_hiRes) + self.header[4]
                    trailer_long = (int((trailer_long - self.header[4])
                                        / (2 * self.acq_channels))
                                    * self.header[12])
                    trailer_item = [trailer_long]
                    if trailer_item[-1] >= 0:
                        time_stamp = True
                else:
                    trailer_long = (trailer_long & 2147483647) - self.header[7]
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
        trailer_comments_dict = {}
        for i in range(self.bytes_in_file - (self.header[4]
                                             + self.adc_data_bytes
                                             + self.header[6]
                                             + self.header[7])):
            trailer_byte = struct.unpack("<b", bin_data.read(1))[0]
            if int(trailer_byte) == 0:
                trailer_comments_dict[i - len(trailer_item)] = (trailer_item)
                trailer_item = ""
            else:
                trailer_item = trailer_item + chr(int(trailer_byte))
        self.trailer.append(trailer_comments_dict)

        bin_data.close()

    # printing list with header values
    def printHeader(self):
        """Prints header of the file"""
        # names of the different header elements
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
            # printing first 33 elements fo the header
            if i < len(field_names):
                print(field_names[i] + ": " + str(self.header[i]))
            else:
                # printing channel information
                print("Channel No. " + str(i - len(field_names))
                      + " information: "
                      + str(self.header[i]))
        # printing control byte at the end of header
        print("Fixed value of 8001H: " + str(self.header[-1]))

    # saves the adc data to a file with name 'name'
    def saveADCsToCSV(self, name, delim=",", header=[]):
        """param name : str \n
        param delim : str, optional \n
        param header : list, optional \n
        Saves the ADC data of the file to a CSV file of name 'name'. \n
        First line of the file will be the header if any is given,
        otherwise it will be empty. \n
        The second line will be the channel number corresponding to
        the channel that recorded the data in the column below. \n
        The third line will be the scaling factor for each channel
        in the column of the respective channel data."""
        # np.savetxt(name, self.adc_data, delimiter = delim, fmt=fmt)
        # writing the adc data to a csv file item by item to save
        # memory
        with open(name, "w", newline="\n") as file:
            # writing header at the top of the file if a header is given
            file.write("#")
            for item in header:
                file.write(str(item))
                file.write(delim)
            file.write("\n")
            # writing channel number for each column at the top of each
            # column
            file.write("#")
            file.write(delim)
            for item in self.channels:
                file.write(str(item))
                file.write(delim)
            file.write("\n")
            # writing the scaling factors at the top of the file
            # scaling information for each channel will be the second
            # item in the column corresponding to that channel after
            # the channel number
            file.write("#")
            file.write(delim)
            for item in self.adc_scaling:
                file.write(str(item))
                file.write(delim)
            file.write("\n")
            # writing adc data and time stamps
            for i, item in enumerate(self.adc_data):
                file.write(str(self.adc_time_stamps[i][-1]))
                file.write(delim)
                for seg in item:
                    file.write(str(seg))
                    file.write(delim)
                file.write(str(self.adc_time_stamps[i][0]))
                file.write(delim)
                file.write(str(self.adc_time_stamps[i][1]))
                file.write("\n")

    # printing the trailer element of the file
    def printTrailer(self):
        """Prints the trailer of the file"""
        print("Event marker pointers: ")
        for item in self.trailer[0]:
            print("Event marked at " + "{:.4f}".format(item[0])
                  + " seconds since start of data acquesition")
            print("Marker created at "
                  + time.strftime("%m-%d-%Y, %H:%M:%S", time.gmtime(item[1]))
                  + " (UTC)")
            try:
                print("Marker comment: " + self.trailer[2][item[2]])
            except:
                pass
            print("")
        print("User annotations")
        for i, item in enumerate(self.trailer[1]):
            print("Channel No. " + str(i) + " annotation: " + str(item))

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
    def printAcqTime(self, az_time=True):
        """Prints time and date of start of
        data acquesition \n
        param az_time: bool, optional \n
            Switches between Arizona time and UTC (default: Arizona time)"""
        # applying a 7 hour offset if az_time is True to account for
        # the 7 hour difference between arizona time and UTC
        if az_time:
            offset = -3600 * 7
        else:
            offset = 0
        print(time.strftime("%d %b %Y , %H:%M:%S",
                            time.gmtime(self.header[13] + offset)))

    # print time and date at which the data acquesition was finished
    # (stored in header[14])
    def printFinishTime(self, az_time=True):
        """"Prints time and date of end of data acquesition \n
        param az_time: bool, optional \n
            Switches between Arizona time and UTC (default: Arizona time)"""
        # applying a 7 hour offset if az_time is True to account for
        # the 7 hour difference between arizona time and UTC
        if az_time:
            offset = -3600 * 7
        else:
            offset = 0
        print(time.strftime("%d %b %Y , %H:%M:%S",
                            time.gmtime(self.header[14] + offset)))

    # print total time in seconds over which the data acquesition took
    # place (1s accuracy)
    def printMeasurementTimeFrame(self):
        """Prints total time in seconds over which the
        data acquesition took place. \n
        The accuracy of this is limited to 1s."""
        print(self.header[14] - self.header[13])

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
        for the channel(s) given in 'number'. \n
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

    # print time between samples
    def printTimeBetweenSamples(self):
        """Prints the time between two ADC data samples"""
        print(self.header[12])

    # prints the sample rate by multiplying the samples per channel
    # per second times the total number of channels
    def printSampleRate(self):
        """Prints total sample rate (samples / s)"""
        print(1 / self.header[12] * self.acq_channels)

    # return total length of header in bytes (stored in header[4])
    def getHeaderLength(self):
        """Returns total length of header in the file in bytes"""
        return self.header[4]

    # return total length of ADC data in bytes (stored in header[5])
    def getADCDataLength(self):
        """Returns total length of ADC data in the file in bytes"""
        return self.header[5]

    # return time and date of start of data acquesition in GMT
    # (stored in header[13])
    def getAcqTime(self, az_time=True):
        """Returns time and date of start of data acquesition \n
        param az_time: bool, optional \n
            Switches between Arizona time and UTC (default: Arizona time)"""
        # applying a 7 hour offset if az_time is True to account for
        # the 7 hour difference between arizona time and UTC
        if az_time:
            offset = -3600 * 7
        else:
            offset = 0
        return time.strftime("%d %b %Y , %H:%M:%S",
                             time.gmtime(self.header[13] + offset))

    # return time and date at which the data acquesition was finished
    # (stored in header[14])
    def getFinishTime(self, az_time=True):
        """"Returns time and date of end of data acquesition \n
        param az_time: bool, optional \n
            Switches between Arizona time and UTC (default: Arizona time)"""
        # applying a 7 hour offset if az_time is True to account for
        # the 7 hour difference between arizona time and UTC
        if az_time:
            offset = -3600 * 7
        else:
            offset = 0
        return time.strftime("%d %b %Y , %H:%M:%S",
                             time.gmtime(self.header[14] + offset))

    # return total time in seconds over which the data acquesition took
    # place (1s accuracy)
    def getMeasurementTimeFrame(self):
        """Returns total time in seconds over which the
        data acquesition took place. \n
        The accuracy of this is limited to 1s."""
        return self.header[14] - self.header[13]

    # return number of acquired channels
    # (stored in last 5 (or 8) bits in header[0])
    def getAcqChannels(self):
        """Returns number of acquired channels"""
        return self.acq_channels

    # return time between samples
    def getTimeBetweenSamples(self):
        """Returns the time between two ADC data samples"""
        return self.header[12]

    # return the sample rate by multiplying the samples per channel
    # per second times the total number of channels
    def getSampleRate(self):
        """Returns total sample rate (samples / s)"""
        return 1 / self.header[12] * self.acq_channels


# only runs if program is run directly from file
if __name__ == "__main__":

    import sys
    import traceback
    import argparse
    desc = """Read CODAS files and translate them to ASCII. The result
    will be separated into the file header, the adc data and the file
    trailer. The header and trailer can be printed to the console and
    the adc data can be saved as a csv file."""
    # setting up argparse with all needed arguments
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.MetavarTypeHelpFormatter)
    parser.add_argument("file", type=str)
    parser.add_argument("-H", "--header", action="store_true",
                        help="Print header of CODAS file")
    parser.add_argument("-t", "--trailer", action="store_true",
                        help="Print trailer of CODAS file")
    parser.add_argument("-p", "--printStartTime", action="store_true",
                        help="Print start time of data acquesition")
    parser.add_argument("-d", "--duration", action="store_true",
                        help="Print duration of data acquesition in seconds")
    parser.add_argument("-r", "--rate", action="store_true",
                        help="Print sample rate")
    parser.add_argument("-a", "--acqChannels", action="store_true",
                        help="Print number of acquired channels")
    parser.add_argument("-s", "--saveADC", action="store_true",
                        help="Save ADC data to csv, required for arguments below")
    parser.add_argument("-c", "--channel", type=int, action="append",
                        help="Add a channel to be read (default: all)")
    parser.add_argument("-b", "--beginTime", type=float,
                        help="""Time in seconds since start of data
                        acquesition at which the first ADC data should
                        be read. (default: 0)""")
    parser.add_argument("-e", "--endTime", type=float,
                        help="""Time in seconds since start of data
                        acquesition at which the last ADC data should
                        be read. (default: until last entry)""")
    parser.add_argument("-n", "--name", type=str,
                        help="""Name for the produced ADC data csv file
                        (default: 'name of file'.csv)""")
    parser.add_argument("-f", "--fileHeader", type=str, action="append",
                        help="""Add an element to the header of the csv file
                        (default: Samples per second = 'sample rate')""")
    input_args = parser.parse_args()

    # setting file location to entered file location and reading
    # header and trailer first (header read automatically)
    location = input_args.file
    try:
        codas_reader = CODASReader(location)
        codas_reader.readTrailer()
        channels = None
        header = header = ["Samples per second = "
                           + str(codas_reader.getSampleRate())]
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    start_time = 0
    end_time = None
    name = location + ".csv"
    # checking all possible command line arguments
    if input_args.header:
        codas_reader.printHeader()
    if input_args.trailer:
        codas_reader.printTrailer()
    if input_args.printStartTime:
        codas_reader.printAcqTime()
    if input_args.duration:
        codas_reader.printMeasurementTimeFrame()
    if input_args.rate:
        codas_reader.printSampleRate()
    if input_args.acqChannels:
        codas_reader.printAcqChannels()
    if input_args.saveADC:
        if input_args.channel:
            channels = input_args.channel
        if input_args.beginTime:
            start_time = input_args.beginTime
        if input_args.endTime:
            end_time = input_args.endTime
        if input_args.name:
            name = input_args.name
        if input_args.fileHeader:
            header = input_args.fileHeader
        try:
            # read and print ADC data with appropriate options
            codas_reader.readADC(channels=channels, start_time=start_time,
                                 end_time=end_time)
            codas_reader.saveADCsToCSV(name=name, header=header)
        except Exception:
            traceback.print_exc()
            sys.exit(1)
    sys.exit()
