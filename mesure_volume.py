#! /usr/bin/env python3
"""
VOLUME CALCULATION STL binary MODELS
Author: Mar Canet (mar.canet@gmail.com) - september 2012
Description: useful to calculate cost in a 3D printing ABS or PLA usage

Modified by:
Author: Saijin_Naib (Synper311@aol.com)
Date: 2016-06-26 03:55:13.879187
Description: Added input call for print material (ABS or PLA), added print of object mass, made Python3 compatible, changed tabs for spaces
Material Mass Source: https://www.toybuilderlabs.com/blogs/news/13053117-filament-volume-and-length

Modified by:
Author: tjblackheart
Date: 2017-07-12
Description: Removed print() calls in favor of json output to use it as a service. Also cleanup.
"""

import os, struct, sys, json

class STLUtils:

    def setMaterial(self, m):
        if m not in {"ABS", "PLA", "CFRP", "Plexiglass"}:
            self.material = "ABS"
        else:
            self.material = m

    def resetVariables(self):
        self.normals = []
        self.points = []
        self.triangles = []
        self.bytecount = []
        self.fb = [] # debug list
        self.output = {"material": self.material}

    # Calculate volume fo the 3D mesh using Tetrahedron volume
    # based in: http://stackoverflow.com/questions/1406029/how-to-calculate-the-volume-of-a-3d-mesh-object-the-surface-of-which-is-made-up
    def signedVolumeOfTriangle(self,p1, p2, p3):
        v321 = p3[0]*p2[1]*p1[2]
        v231 = p2[0]*p3[1]*p1[2]
        v312 = p3[0]*p1[1]*p2[2]
        v132 = p1[0]*p3[1]*p2[2]
        v213 = p2[0]*p1[1]*p3[2]
        v123 = p1[0]*p2[1]*p3[2]
        return (1.0/6.0)*(-v321 + v231 + v312 - v132 - v213 + v123)

    def unpack(self, sig, l):
        s = self.f.read(l)
        self.fb.append(s)
        return struct.unpack(sig, s)

    def read_triangle(self):
        n  = self.unpack("<3f", 12)
        p1 = self.unpack("<3f", 12)
        p2 = self.unpack("<3f", 12)
        p3 = self.unpack("<3f", 12)
        b  = self.unpack("<h", 2)

        self.normals.append(n)
        l = len(self.points)
        self.points.append(p1)
        self.points.append(p2)
        self.points.append(p3)
        self.triangles.append((l, l+1, l+2))
        self.bytecount.append(b[0])

        return self.signedVolumeOfTriangle(p1,p2,p3)

    def read_length(self):
        length = struct.unpack("@i", self.f.read(4))
        return length[0]

    def read_header(self):
        self.f.seek(self.f.tell()+80)

    def cm3_To_inch3Transform(self, v):
        return v*0.0610237441

    def calculateMassCM3(self,totalVolume):
        totalMass = 0
        if self.material in {"1","ABS"}:
            totalMass = (totalVolume*1.04)
        elif self.material in {"2","PLA"}:
            totalMass = (totalVolume*1.25)
        elif self.material in {"3","CFRP"}:
            totalMass = (totalVolume*1.79)
        elif self.material in {"4","Plexiglass"}:
            totalMass = (totalVolume*1.18)

        return totalMass

    def calculateVolume(self, infilename, unit):
        self.resetVariables()
        totalVolume = 0
        totalMass = 0

        try:
            self.f = open( infilename, "rb")
            self.read_header()
            l = self.read_length()
            self.output["triangles"] = l

            try:
                while True:
                    totalVolume += self.read_triangle()
            except Exception as e:
                pass

            totalVolume = (totalVolume/1000)
            totalMass = self.calculateMassCM3(totalVolume)

            if totalMass == 0:
                self.output["mass"] = 0
            else:
                self.output["mass"] = totalMass

            if unit == "cm":
                self.output["volume"] = totalVolume
            else:
                totalVolume = self.cm3_To_inch3Transform(totalVolume)

        except Exception as e:
            print(json.dumps({"error":e}))

        print(json.dumps(self.output))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error":"Usage: "+os.path.basename(sys.argv[0])+" <FILE.STL> <ABS|PLA|CFRP|Plexiglass>"}))
    else:
        mySTLUtils = STLUtils()
        mySTLUtils.setMaterial(sys.argv[2])
        mySTLUtils.calculateVolume(sys.argv[1], "cm")
