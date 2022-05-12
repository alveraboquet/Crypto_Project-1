import matplotlib.pyplot as plt

VALUE = [0, 1, 2, 3, 4, 5]

plt.figure()
plt.plot(VALUE, color="green")
plt.xlabel("Date & Time")
plt.ylabel("Value $")
# plt2=plt.twinx()
# plt2.plot(HYPE)
# #plt2.plot(HYPE.diff(periods=1))
# #plt2.plot(HYPE.diff(periods=2))
# plt2.set_ylabel("Hype %")
# plt2.legend(['Close price'])
plt.legend(['Buy Indicator', 'differential 1', 'differential 2'])
plt.show()
