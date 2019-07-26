import glob
import os
import sys
import time


configuration_file = sys.argv[1]
input_dir = sys.argv[2]
output_dir = sys.argv[3]

input_files = glob.glob(input_dir + '/*.txt')

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

time.sleep(8)
for input_file in input_files:
    input_file = input_file.replace('\\', '/')
    input_file_blank = input_file.split('/')[-1].replace('.txt', '')
    with open(input_file, 'r') as in_f:
        with open(f'{output_dir}/{input_file_blank}_2.txt', 'w+') as out_f:
            in_line = in_f.readlines()
            out_f.write('{in_line}_2')
            out_f.close()
