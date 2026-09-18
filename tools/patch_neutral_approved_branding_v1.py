#!/usr/bin/env python3
from pathlib import Path
import binascii, math, struct, sys, zlib

root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')
branding=root/'assets'/'branding'
branding.mkdir(parents=True,exist_ok=True)

def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',binascii.crc32(kind+data)&0xffffffff)

def segdist(px,py,x1,y1,x2,y2):
    dx=x2-x1; dy=y2-y1
    den=dx*dx+dy*dy
    if den==0: return math.hypot(px-x1,py-y1)
    t=max(0,min(1,((px-x1)*dx+(py-y1)*dy)/den))
    return math.hypot(px-(x1+t*dx),py-(y1+t*dy))

def inside_poly(x,y,pts):
    c=False
    j=len(pts)-1
    for i in range(len(pts)):
        xi,yi=pts[i]; xj,yj=pts[j]
        if ((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/(yj-yi+1e-9)+xi):
            c=not c
        j=i
    return c

def draw(path,size=384,transparent=True):
    scale=size/384
    def S(v): return v*scale
    bg=(255,255,255,0 if transparent else 255)
    navy=(0,74,137,255)
    teal=(0,166,166,255)
    green=(38,184,72,255)
    white=(255,255,255,255)
    rows=[]
    shield=[(192,40),(309,103),(309,210),(282,283),(192,345),(102,283),(75,210),(75,103)]
    inner=[(192,67),(286,118),(286,204),(263,263),(192,313),(121,263),(98,204),(98,118)]
    for yy in range(size):
        row=bytearray([0])
        y=yy/scale
        for xx in range(size):
            x=xx/scale
            color=bg
            if inside_poly(x,y,shield):
                # subtle approved-logo blue->teal split
                color=navy if x < 192 else teal
            if inside_poly(x,y,inner):
                color=white
            # hardhat dome + brim
            if ((x-192)/70)**2+((y-145)/55)**2 <= 1 and y>=108 and y<=161:
                color=navy
            if 122<=x<=262 and 155<=y<=171:
                color=navy
            if 174<=x<=187 and 95<=y<=145: color=white
            if 197<=x<=210 and 95<=y<=145: color=white
            # clipboard body border
            if 116<=x<=268 and 176<=y<=279:
                if x<128 or x>256 or y<188 or y>267: color=navy
                else: color=white
            # checklist green ticks
            for cy in (207,236,265):
                if segdist(x,y,142,cy,153,cy+11)<=4 or segdist(x,y,153,cy+11,171,cy-8)<=4:
                    color=green
                if segdist(x,y,183,cy+2,235,cy+2)<=4:
                    color=navy
            # large diagonal green check
            if segdist(x,y,155,286,190,321)<=13 or segdist(x,y,190,321,305,207)<=13:
                color=green
            row.extend(color)
        rows.append(bytes(row))
    raw=b''.join(rows)
    png=b'\x89PNG\r\n\x1a\n'
    png+=chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,6,0,0,0))
    png+=chunk(b'IDAT',zlib.compress(raw,9))
    png+=chunk(b'IEND',b'')
    path.write_bytes(png)

draw(branding/'sst_icon.png',transparent=False)
draw(branding/'sst_icon_transparent.png',transparent=True)
draw(branding/'sst_logo.png',transparent=False)
print('SST_BRANDING_APROVADA_OK: novo escudo com capacete, checklist e check verde aplicado.')
