import struct

location = "Desktop/BinaryReader/Files/d20190923/20190923-T1.wdq"
bin_data = open(location, "rb")
formats1 = ["H", "H", "b", "b", "h", "L", "L", "h", "H", "H", "l", "4b", "d",
 "l", "l", "l", "l", "l", "l", "h", "h", "b", "b", "b", "b", "32b", "H", "H", "b", "b", "i", "b", "b"]
values = []

for form in formats1:
    values.append(struct.unpack(form, bin_data.read(struct.calcsize(form))))

for i in range(110, values[4][0] - 3):
    values.append(struct.unpack("36b", bin_data.read(struct.calcsize("36b"))))
    i = i + 36

values.append(struct.unpack("h", bin_data.read(struct.calcsize("h"))))


print(values, len(values))