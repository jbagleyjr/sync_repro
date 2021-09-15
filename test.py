#!/usr/bin/python3

file = open("time.txt")
string = file.read().replace("\n", " ")
file.close()

print('time is ' + string)

