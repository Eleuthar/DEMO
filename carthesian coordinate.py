from math import hypot


class Point:
    def __init__(self, x=0.0, y=0.0):
        self.__x = float(x)
        self.__y = float(y)
        self.__point = float(hypot(self.__x, self.__y))

    def getx(self):
        return self.__x
        

    def gety(self):
        return self.__y
        

    def distance_from_xy(self, x, y):        
        self.point2 = hypot(x, y)
        return hypot(self.__point, self.point2)
        

    def distance_from_point(self, point):
        self.pointB = hypot(point.getx(), point.gety())
        return hypot(self.__point, self.pointB)

        


class Triangle:
    def __init__(self, vertice1, vertice2, vertice3):
        self.vertice1 = vertice1
        self.vertice2 = vertice2
        self.vertice3 = vertice3

        
    def perimeter(self):
        self.zid1 = self.vertice1.distance_from_point(self.vertice2)
        self.zid2 = self.vertice1.distance_from_point(self.vertice3)
        self.zid3 = self.vertice3.distance_from_point(self.vertice2)
        return self.zid1 + self.zid2 + self.zid3
            


triangle = Triangle(Point(0, 0), Point(1, 0), Point(0, 1))
print(triangle.perimeter())
