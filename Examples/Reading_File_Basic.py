from CODASReader import CODASReader

file_location = "ExampleFiles/20190923-T1.wdq"
# intilize new CODASReader with the specififed file
# this reads the file header automatically
reader = CODASReader(file_location)
# reading the ADC data
reader.readADC()
# reading the file trailer
reader.readTrailer()

# printing the file header and file trailer
reader.printHeader()
print("\n\n")
reader.printTrailer()
print("\n\n")

# saving the ADC data to a CSV file
# of the same name as the original file
reader.saveADCsToCSV(file_location + ".csv")

# for more information on the CODASReader class methods
# please consult the README.md or use help(CODASReader)

help(CODASReader)