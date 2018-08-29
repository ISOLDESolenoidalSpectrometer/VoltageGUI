# mhv4lib
A simple Python3 library to control a Mesytec MHV-4 bias voltage unit using the built-in USB serial communication interface.

## Prerequisites

Required libraries etc.
* Python 3.x
* pyserial  (Only pyserial should be installed on the system! Check with 'pip3 list'. To uninstall other serial libraries such as 'serial', use 'sudo pip3 uninstall serial')
* wxPython 4.x (Optional, required only for the GUI example no. 4)
* numpy (Optional, required for example no. 2)

Installing these python libraries can be done with the pip3-command (install pip3 for Python3 first):

	sudo pip3 install pyserial wxpython numpy

Note: Compiling wxPython may require additional libraries depending on your operating system.

## MHV-4 Documentation
More information on the MHV-4 module and the data protocol can be found here:

	https://www.mesytec.com/products/nuclear-physics/MHV-4.html
	
	https://www.mesytec.com/products/datasheets/MHV-4.pdf


Screenshot of Example 4 wxPython GUI running:

![alt text](https://raw.githubusercontent.com/jopekonk/mhv4lib/master/example4_mhv4gui_screenshot.png)
