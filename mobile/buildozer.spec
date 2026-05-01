[app]
title = Production Accounting Mobile
package.name = pas_mobile
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,ttf,txt
version = 1.0.0

orientation = portrait
android.permissions = INTERNET,CAMERA,RECORD_AUDIO

[buildozer]
log_level = 2
warn_on_root = 1

requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,plyer,urllib3,chardet,idna,certifi

[app@android]
# p4a.branch = master
