# -*- coding: utf-8 -*-
"""
Python Library to launch Spark3D simulations. 
Usefull to make batch calculations. 

Created on Mon Apr  7 16:49:00 2014

@author: J.Hillairet
"""
import os
import numpy as np 
import fileinput
from subprocess import PIPE, Popen
import pandas as pd

def printc(message, color='red'):
    if color in ('red','r'):
        escape_code = '\x1b[31m'
    if color in ('blue', 'b'):
        escape_code = '\x1b[34m'
    if color in ('green', 'g'):
        escape_code = '\x1b[32m'
    if color in ('magenta', 'm'):
        escape_code = '\x1b[35m'
    if color in ('cyan', 'c'):
        escape_code = '\x1b[36m'
    normal_code = '\x1b[0m'
    print(escape_code+message+normal_code)

class Spark3d(object):
    """
    SPARK3D simulation object
    
    IMPORTANT : 
    The 'path-to-spark3D/dist/' directory should added 
    in the user LD_LIBRARY_PATH environment variable.
    
    Moreover, a 'config.min' file and a 'results/' directory 
    should be present in the project directory.
    
    
    """
    # Absolute path of the 'spark3d' binary file
    SPARK_PATH = '/Home/JH218595/Spark3D/SPARK3D-1.6.3-full-Linux/'
    BIN_PATH = SPARK_PATH + 'dist/spark3d'

    
    def __init__(self, project_path, data_file, file_type='hfss', 
                 output_path='results/', tmp_path='tmp/', 
                 config_file='config.min'):
        """
        Constructor.
        
        Arguments
        ---------
         project_path : string
             absolute path (important!) of the project. 
         data_file : string
             relative path of the data file
         [file_type : {'hfss' (default),'cst','csv'}] Take care to the model units : mm !
         [output_path: relative path of the output dir (default: "results/")]
         [tmp_path: temporary file relative path (default: 'tmp/')]
         [config_file]: config filename (default: 'config.min')
        
        """  
        self.file_type = file_type
        if not file_type in ('hfss', 'cst', 'csv'):
            raise ValueError("Bad file type. Should be 'hfss','cst' or 'csv'")
            
        self.project_path = project_path                
        if not os.path.exists(project_path):
            raise OSError('Incorrect project directory (absolute) path') 
            
         # Spark3D configuration filename
        self.config_file = config_file
        if not os.path.isfile(os.path.join(project_path, config_file)):
            print(os.path.join(project_path, config_file))
            raise OSError('Incorrect (relative) configuration filename')
        
        self.data_file = data_file
        if not os.path.isfile(os.path.join(project_path, data_file)):
            print(os.path.join(project_path, data_file))
            raise OSError('Incorrect data file (relative) path')
        
        self.tmp_path = tmp_path    
        if not os.path.exists(os.path.join(project_path, tmp_path)):
            raise OSError('Incorrect  temp directory (relative) path')
            
        self.output_path = output_path 
        if not os.path.exists(os.path.join(project_path, output_path)):
            raise OSError('Invalid output directory (relative) path')
            
        # The default results file should be the following
        self.results_file = os.path.join(project_path, output_path, 'general_results.txt')            
    
    def run(self):
        """
        Run the SPARK3D modeling. 
        
        """
        try:
            # Add the Spark3D library dir to the PATH
            env = os.environ
            if 'Spark3D' not in env['LD_LIBRARY_PATH']:
                env['PATH'] = os.path.join(self.SPARK_PATH, 'dist')+ ':' + env['PATH']
                env['LD_LIBRARY_PATH'] = os.path.join(self.SPARK_PATH, 'dist') + ':' + env['LD_LIBRARY_PATH']
            
            
            #retcode = call(self._get_run_command(), shell=True)
            
            # retcode = check_output(self._get_run_command(), 
            #                        shell=True, env=env)
            # Runs the process and print the output in the python shell
            print(self._get_run_command()+'\n')
            with Popen(self._get_run_command(), shell=True, env=env, 
                       stdout=PIPE, stderr=PIPE, universal_newlines=True) as p:
                for lines in p.stdout:
                    print(lines, end=' ')
            print(p.returncode)                  
        except OSError as e:
            print('Error ! '+e)
                  
    def _get_run_command(self):
        
        cmd = self.BIN_PATH + \
              ' --tmp_path='+self.tmp_path + \
              ' --mode=multipactor' + \
        	  ' --project_path='+self.project_path + \
        	  ' --config_file='+self.config_file + \
        	  ' --output_path='+self.output_path + \
        	  ' --data_file='+self.data_file + \
              ' --file_type='+self.file_type + \
              ' --HFSS_units="mm"'
              
        return(cmd)
        
    
    def get_results(self):
        """
        Returns the SPARK3D run results
        
        Arguments
        ----------
         none
        
        Returns
        ----------
         freq: array of frequency
         power: array of breakdown power
         
        """
        freq, power = None, None
        if os.path.isfile(self.results_file):
            freq, power = np.loadtxt(self.results_file, 
                               skiprows=1, 
                               delimiter='\t', 
                               usecols=(3,4), # use only columns 3 and 4
                               unpack=True)

        self.freq = freq
        self.power = power        
        return freq, power 


    def get_full_results(self):
        """
        Returns the SPARK3D full results
        
        Returns
        ---------
         power_results : pandas DataFrame 
                         Various power tested and multipactor orders
         time_results: pandas DataFrame
                         nb of electrons vs time for each power tested
        
        """
        power_results, time_results = [], []
        full_res_dir = os.path.join(self.project_path, self.output_path, 'region1', 'signal1')

        power_results_file = os.path.join(full_res_dir, 'power_results.txt')
        print(power_results_file)
        if os.path.isfile(power_results_file):
            power_results = pd.read_csv(power_results_file, delimiter='\t', index_col='#Power (W)', na_values='---')
        
        time_results_file = os.path.join(full_res_dir, 'time_results.txt') 
        print(time_results_file)
        if os.path.isfile(time_results_file):
            time_results = pd.read_csv(time_results_file, delimiter='\t')

        self.power_results = power_results
        self.time_results = time_results
        return power_results, time_results

    def set_config_parameter(self, param, value):
        config_filename = os.path.join(self.project_path, self.config_file)
        
        with fileinput.FileInput(config_filename, inplace=True, backup='.bak') as file:
            for line in file:
                if param in line:
                    print('  {}\t\t{}'.format(param, value))
                else:
                    print(line, end='')
        
    def get_config_parameter(self, param):
        config_filename = os.path.join(self.project_path, self.config_file)
        
        value = []
        with fileinput.FileInput(config_filename) as file:
            for line in file:
                if param in line:
                    value = float(line.split()[1])
                    print(value)
       
        return value
           
if __name__ == "__main__":  
    # Absolute path of the project
    project_path = '/ZONE_TRAVAIL/JH218595/Spark3D/Simple_Waveguide_WR284_3.7GHz/'
    # Relative path to the .dsp file    
    data_file = 'data_HFSS/SimpleWaveguideFields_72.14x22mm_100mm_V2.dsp'  
    config_file = 'config.min'
    # Run the Spark3D Simulation    
    spk = Spark3d(project_path, data_file, config_file=config_file)     
    spk.run()
    freq, power = spk.get_results()
    print(freq, power)
    
    # Appending the results to a text file
    with open('RESULTS.txt','ba') as f_handle:
        np.savetxt(f_handle, [power])