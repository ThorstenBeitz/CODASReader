from CODASReader import CODASReader

file_location = "ExampleFiles/20190923-T1.wdq"
# intilize new CODASReader with the specififed file
# this reads the file header automatically
reader = CODASReader(file_location)

# read file trailer
reader.readTrailer()

# print the number of acquired channels
# channels that can be selected to be read are between 0 and
# the number of acquired channels - 1 (inclusive)
reader.printAcqChannels()
# print the start and end time and date of data acquesition
reader.printAcqTime()
reader.printFinishTime()
# print the duration of the data acquesition in seconds
reader.printMeasurementTimeFrame()
# selecting a start and end time between which the ADC data
# should be read and later saved.
# Both the start as well as the end time are in seconds since
# the start of data acquesition (float).
start_time = 5
# setting the end time to be 13.8 seconds before the end of data
# acquesition
end_time = reader.getMeasurementTimeFrame() - 13.8
# setting a list of channels that should be read.
# in this case only channel one will be read (index 0)
channels = [0]
# print the sample rate of the recorded data in samples/s
reader.printSampleRate()
# setting up a custom header for the CSV file.
# In this case it contains the sample rate
# and the start time and date
header = [
    "sample rate = " + str(reader.getSampleRate()),
    "start time of acquesition: " + str(reader.getAcqTime())
]
# reading the ADC data from specified channels
# and between specified times
reader.readADC(
    channels=channels,
    start_time=start_time,
    end_time=end_time
)

# print the file header and trailer
print("\n\n")
reader.printHeader()
print("\n\n")
reader.printTrailer()
print("\n\n")

# save ADC data to a file of the same name as original file
# with the custom header specified
# only the data read before, i.e with specified channels and times
# will be saved
reader.saveADCsToCSV(
    file_location + ".csv",
    header=header
)

# a description of the format of the produced CSV file
# as well as further information on the CODASReader class
# can be found in the README.md file