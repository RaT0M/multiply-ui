#!/home/tonio-bc/.conda/envs/multiply-platform-dev/bin/python
# example syntax: retr_prior.py workshop-test.yaml /data/m5/priors

from multiply_prior_engine import PriorEngine
import datetime
import os
import sys
import yaml

# setup parameters
configuration_file = sys.argv[1]
start = sys.argv[2]
end = sys.argv[3]
output_root_dir = sys.argv[4]

# read request file for parameters
with open(configuration_file) as f:
    parameters = yaml.load(f)
processor_dir = '/software/prior-engine-0.5/multiply_prior_engine'

#start_time = parameters['General']['start_time']
#end_time = parameters['General']['end_time']
variables =  parameters['Inference']['parameters']

start_time = datetime.datetime.strptime(start, '%Y-%m-%d')
end_time = datetime.datetime.strptime(end, '%Y-%m-%d')

# execute the Prior engine for the requested times
time = start_time
while time<=end_time:
    print(time)
    PE = PriorEngine(config=configuration_file, datestr=time.strftime('%Y-%m-%d'), variables=variables)
    priors = PE.get_priors()
    time = time + datetime.timedelta(days=1)

# create output_dir (if not already exist)
if not os.path.exists(output_root_dir):
    os.makedirs(output_root_dir)

# put the files for the 'vegetation priors' into the proper directory
if 'General' in parameters['Prior']:
    directory = parameters['Prior']['output_directory']
    os.system("cp "+directory+"/*.vrt " +output_root_dir+"/")

# put the files for the 'soil moisture' into the proper directory
#if 'sm' in parameters['Prior']:
#    ptype = parameters['Prior']['sm']
#    if 'climatology' in ptype:
#        soil_moisture_dir = parameters['Prior']['sm']['climatology']['climatology_dir']
    #soil_moisture_dir = '/data/auxiliary/priors/Climatology/SoilMoisture'
#    else:
#        soil_moisture_dir = parameters['Prior']['General']['directory_data']
#    os.system("mv " + soil_moisture_dir + "/*.vrt " + output_root_dir + "/")

