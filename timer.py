class Timer:
    def __init__( self, hourz=0, minutz=0, zecondz=0 ):
        self.hourz = hourz
        self.minutz = minutz
        self.zecondz = zecondz
        
        
        
    def __str__(self):
        x = [self.hourz, self.minutz, self.zecondz]
        self.strObj = ''
        for z in range(len(x)):
            if z != 2:
                if x[z] < 10:
                    self.strObj += "0"+ str(x[z]) + ":"
                else:
                    self.strObj += str(x[z]) + ":"
            else:
                if x[z] < 10:
                    self.strObj += "0"+ str(x[z])
                else:
                    self.strObj += str(x[z])
        return self.strObj
        

    def next_second(self):
        if self.zecondz == 59:
            self.zecondz = 0
            if self.minutz == 59:
                self.minutz = 00
                if self.hourz == 23:
                    self.hourz = 0
        else:
            self.zecondz += 1

        
    def prev_second(self):
        if self.zecondz == 0:
            self.zecondz = 59
            if self.minutz == 0:
                self.minutz = 59
                if self.hourz == 0:
                    self.hourz = 23
        else:
            self.zecondz -= 1



timer = Timer(23, 59, 59)
print(timer)
timer.next_second()
print(timer)
timer.prev_second()
print(timer)
