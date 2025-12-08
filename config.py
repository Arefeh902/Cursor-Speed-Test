
# Paths
INPUT_FILE_PATH = './test_input.csv'
OUTPUT_DIR = './test_results/'
DATA_DIRECTORY =  "data"

# Origin x and y
ORIGIN_X = 25                               # cm
ORIGIN_Y = 8.84                             # cm

# Test Parameters
DELAY_BETWEEN_TESTS = 1500                  # ms
MAX_SPEED_OVERSHOOT_COEFFICIENT = 0.03
NUM_OF_POINTS_WITH_LESS_THAN_MAX_SPEED = 10
PERCENT_OF_POINTS_TO_PROCESS_FOR_OVERSHOOT_AND_UNDERSHOOT = 0.80

# Form Params
FORM_OPTIONS_TYPES = ['C1', 'C2', 'P1', 'P2','PR1', 'PR2', 'W1', 'W2', 'WR1', 'WR2', 'Pre-Test', 'Post-Test', 'Transfer']

# Visual Parameters
SOURCE_CIRCLE_COLOR      = (120, 245, 66)       
DESTINATION_CIRCLE_COLOR = (120, 245, 66)  
MIDDLE_CIRCLE_COLOR      = (240, 234, 0)       
RECT_COLOR               = (66, 209, 245)                 
BACKGROUND_COLOR         = (255, 254, 212) 
SUCCESS_PATH_COLOR       = (0, 255, 0) 
RECT_HIT_PATH_COLOR       = (255, 0, 0) 
UNDERSHOOT_PATH_COLOR    = (255, 0, 0) 
OVERSHOOT_PATH_COLOR     = (255, 0, 0) 


# Beep Sounds
START_FREQUENCY     = 500
START_DURATION_MS   = 0.35             # sec
SUCCESS_FREQUENCY   = 750
SUCCESS_DURATION_MS = 0.35             # sec
FAILURE_FREQUENCY   = 1000
FAILURE_DURATION_MS = 0.35             # sec

