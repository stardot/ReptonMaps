__all__ = ["levels", "sprites"]

import UEFfile

class NotFound(Exception):
    pass

class IncorrectSize(Exception):
    pass

class Repton:

    def __init__(self, uef_file):
    
        self.u = UEFfile.UEFfile(uef_file)
        
        for details in self.u.contents:

            if details["name"] == "REPTON2":
                break
        else:
            raise NotFound
        
        self.data = details["data"]
        
        if len(self.data) != 0x4a00:
            raise IncorrectSize
    
    def read_level_data(self):
    
        return self.data[0x2c00:]
    
    def read_sprite_data(self):
    
        #return self.data[0x2500:0x26b0]
        return self.data[0x2500:0x2c00]
