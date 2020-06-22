import struct

location = "Desktop/BinaryReader/Files/d20190923/20190923-T1.wdq"
bin_data = open(location, "rb")
formats = ["H", "H", "b", "b", "h", "I", "I", "h"]
values = []

for form in formats:
    values.append(struct.unpack(form, bin_data.read(struct.calcsize(form))))

print(values)