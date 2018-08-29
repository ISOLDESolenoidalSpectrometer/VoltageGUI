class Element:
	def __init__(self, number):
		self.channel = number
		self.next = None
		self.parent=None

class Element2:
	def __init__(self, number,option,value):
		self.channel = number
		self.next = None
		self.parent=None
		self.option=option #Option 0: Polarity Change, Option 1: Enable/Disable
		self.value=value #determines whether new polarity is positive/negative...


class DoubleQueue:
	def __init__(self):
		self.root=None
	
	def add(self,element):
		if self.root==None:
			self.root=element
		else:
			current=self.root
			while(current.next!=None):
				current=current.next

			current.next=element
			element.parent=current
	
	def remove(self,element):
		if self.root==element:
			if element.next!=None:
				self.root=element.next
			else:
				self.root=None
			element=None
		else:
			if element.next==None:
				element.parent.next=None
				element=None
			else:
				element.parent.next=element.next
				element.next.parent=element.parent
				element=None
	def isEmpty(self):
		if self.root==None:
			return True
		else:
			return False

	def Print(self):
		current=self.root
		while current!=None:
			print(current.channel)
			current=current.next



