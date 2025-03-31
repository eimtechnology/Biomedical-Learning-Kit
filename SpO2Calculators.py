class AcDcCalculator:
    def __init__(self, threshold_percentage) -> None:
        self.threshold_percentage = threshold_percentage
        self.peak_indexes = []
        self.valley_indexes = []
        self.total_indexes = []
        self.peaks = []
        self.valleys  = []
        self.looking_for_peaks = True
        self.greatest_peak = 0
        self.lowest_valley = 90000        
        self.peak_threshold = 0
        self.valley_threshold = 0
        self.true_peak = 0
        self.true_peak_index = 0
        self.true_valley = 90000
    
    
    def peak_valley_detection(self, sample, sample_index):

        if len(self.valleys) != 0 and len(self.valley_indexes) != 0:
            if self.looking_for_peaks:
                if sample > self.greatest_peak:                    
                    self.greatest_peak = sample
                    self.index_interest = sample_index                   
                    if self.greatest_peak - self.valleys[-1] < 1000:
                        self.valley_threshold = self.threshold_percentage * (self.greatest_peak - self.valleys[-1])                    
                elif sample < self.greatest_peak - self.peak_threshold:
                   
                    #print(str(self.index_interest) + "," + str(self.greatest_peak) + '\n')
                    self.true_peak = self.greatest_peak
                    self.true_peak_index = self.index_interest
                    #self.peaks.append(self.greatest_peak)
                    
                    '''print("threshold for new valley: ", self.valley_threshold, "value needs to go below: ", self.peaks[-1] - self.valley_threshold)
                    print("greatest peak at: ", self.index_interest)
                    print("declared at sample: ", sample_index)'''

                    self.greatest_peak = 0
                    self.looking_for_peaks = False
                    self.peak_indexes.append(self.index_interest)
                    self.total_indexes.append(self.index_interest)

                    

                    # print("valleys: ", self.valley_indexes)
                    # print("peaks: ", self.true_peak_index)
                    return 1

                    
                
            else:
                if sample < self.lowest_valley:
                    #print("new lowest valley: ", sample, sample_index)
                    self.lowest_valley = sample
                    self.index_interest = sample_index        
                    if self.true_peak - self.lowest_valley < 1000:
                        self.peak_threshold = self.threshold_percentage * (self.true_peak - self.lowest_valley)                                
                elif sample > self.lowest_valley + self.valley_threshold:        
                    
                    #print(str(self.index_interest) + "," + str(self.lowest_valley) + '\n')
                    self.valleys.append(self.lowest_valley)
                    #self.threshold = self.threshold_percentage * (self.peaks[-1] - self.valleys[-1])
                    '''print("threshold for new peak: ", self.peak_threshold, "value needs to exceed: ", self.valleys[-1] + self.peak_threshold)
                    print("lowest valley at: ", self.index_interest)
                    print("declared at sample: ", sample_index)'''

                    self.looking_for_peaks = True
                    self.valley_indexes.append(self.index_interest)
                    self.total_indexes.append(self.index_interest)
                    self.true_valley = self.lowest_valley
                    self.lowest_valley = 90000

                    if len(self.valley_indexes) > 2:
                        self.valley_indexes.pop(0)
                        self.valleys.pop(0)
                    # print("valleys: ", self.valley_indexes)
                    # print("peaks: ", self.true_peak_index)

                    return 2         
                
                    #print(self.valley_indexes)
        else:
            self.valleys.append(sample)
            self.valley_indexes.append(sample_index)
        
                
    
    
    def report_peek_valleys(self):
        print("peaks: ", self.peaks)
        print("valleys: ", self.valleys)
    
    def calculate_ratio(self):
        if len(self.valley_indexes) >= 2 and len(self.valleys) >= 2:
            if self.valley_indexes[0] < self.true_peak_index and self.valley_indexes[1] > self.true_peak_index:
                
                slope = (self.valleys[1] - self.valleys[0])/(self.valley_indexes[1] - self.valley_indexes[0])

                cross_y = slope*(self.valley_indexes[0] - self.true_peak_index) - self.valleys[0]
                cross_y = cross_y * -1 

                dc = cross_y
                ac = self.true_peak - cross_y

                return float(ac/dc)
            
    def reset(self):
        self.peak_indexes = []
        self.valley_indexes = []
        self.total_indexes = []
        self.peaks = []
        self.valleys  = []
        self.looking_for_peaks = True
        self.greatest_peak = 0
        self.lowest_valley = 90000        
        self.peak_threshold = 0
        self.valley_threshold = 0
        self.true_peak = 0
        self.true_peak_index = 0

def calculate_SpO2(ir_ratio, red_ratio):
    r = red_ratio/ir_ratio
    return 104 - 17*r  