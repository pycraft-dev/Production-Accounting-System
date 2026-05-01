[app]
title = Production Accounting Mobile
package.name = pas_mobile
package.domain = org.example

[buildozer]
log_level = 2
warn_on_root = 1

requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,plyer,urllib3,chardet,idna,certifi
android.permissions = INTERNET,CAMERA,RECORD_AUDIO

orientation = portrait

[app@android]
# p4a.branch = master
