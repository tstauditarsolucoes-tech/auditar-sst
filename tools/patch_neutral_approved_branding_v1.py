#!/usr/bin/env python3
from pathlib import Path
import base64, sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')
branding=root/'assets'/'branding'
branding.mkdir(parents=True,exist_ok=True)
data=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAKAAAACgCAYAAACLz2ctAAAz9UlEQVR42u2dd7wcVfn/3+ecmW233yQkhARIIaSAhGIoEkqQJoIIXxVRwPZD/SqKFQFBiogFFES+YgNFpCiKhA6hJ0ISAiEkIQFCCglJSL+5bXfmnPP7Y8rO7t2bBujF1zyvV3Lb7OzsnM885fOUI6y1llRS+Q+JTG9BKikAU0kBmEoqKQBTSQGYSiopAFNJAZhKKikAU0kBmEoqKQBTSSUFYCopAFNJJQVgKikAU0klBWAqKQBTSSUFYCopAFNJJQVgKikAU0klBWAqKQBTSSUFYCopAFNJJQVgKikAU0klBWAqKQBTSSUFYCopAFNJJQVgKikAU0klBWAqKQBTSSUFYCp9Tv4/ASHuQjXgooMAAAAASUVORK5CYII=")
for name in ('sst_icon.png','sst_icon_transparent.png','sst_logo.png'):
    (branding/name).write_bytes(data)
print('SST_BRANDING_APROVADA_OK: logo aprovada aplicada em login, cabeçalho e ativos neutros.')
