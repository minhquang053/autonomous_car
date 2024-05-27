class Ultrasonic:
    def __init__(self, Ab):
        self.Ab = Ab
            
    def measure_distances(self):
        return [(int(dist) if dist < 100 else 100) if dist >= 0 else 0 for dist in self.Ab.SR04()]
