import subprocess as sp
import math, string

class AlprCaller():
    def __init__(self, country_code, image_name):  # Country code is eu or us
        self.country_code = country_code
        self.image_name = image_name

    def get_license_plate_text(self):
        try:
            text = str(sp.check_output(['alpr', '-c ', str(self.country_code), self.image_name])).strip('b').split('-')
            text=text[1:]
        except sp.CalledProcessError:
            text = math.pi
            return text
        if text:
            text = [i.strip().strip('\\n').split('\\t confidence: ') for i in text][0]  # Only get guess with highest probability
            text= tuple((text[0] ,float(text[1])))
        else:
            text = math.pi
            return text

        return text

# A = AlprCaller('eu','das638.jpeg')
# txt = A.get_license_plate_text()
# print(txt)
