import csv

class ResultsWriter:
    def __init__(self, filename):
        self.filename = filename

    def write_results(self, results):
        with open(self.filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            # Write the header only if the file is empty
            if file.tell() == 0:
                writer.writerow(['image_name', 'shape', 'letter', 'center_x', 'center_y', 'detection_confidence', 'classification_confidence'])
            
            for result in results:
                writer.writerow([
                    result['image_name'], 
                    result['shape'], 
                    result['letter'], 
                    result['center_x'], 
                    result['center_y'], 
                    result['detection_confidence'], 
                    result['classification_confidence']
                ])

# Example usage:
# results = [
#     {'image_name': 'img1.png', 'shape': 'circle', 'letter': 'A', 'center_x': 50, 'center_y': 100, 'detection_confidence': 0.95, 'classification_confidence': 0.98},
#     {'image_name': 'img2.png', 'shape': 'square', 'letter': 'B', 'center_x': 60, 'center_y': 110, 'detection_confidence': 0.90, 'classification_confidence': 0.93}
# ]
# writer = ResultsWriter('results.csv')
# writer.write_results(results)