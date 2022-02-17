import sys
from sejong import getFromYear

if len(sys.argv) < 2 or 4 < len(sys.argv):
    print("Insufficient arguments")
    sys.exit()

year = int(sys.argv[1])
start = 0
end = 15

if len(sys.argv) > 2:
    start = int(sys.argv[2])
if len(sys.argv) > 3:
    end = int(sys.argv[3])

print(f"Program Start, year={year} start={start} end={end}")
# getFromYear(0, start=0, end=3)
