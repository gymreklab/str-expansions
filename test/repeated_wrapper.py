# This is the wrapper for the STR experiments.
# This script will take care of creating directories, and calls
# other scripts as necessary.
# Parsing and creating paths is dealt with in this script.

import errno    
import os
import sys
import subprocess

import argparse

def find_motif_refAll(locus):
	with open(locus, 'r') as f:
		line = f.read().split()
		return line[5], int(line[4])


parser = argparse.ArgumentParser('Filter sam/bam files to only keep spanning reads.')
parser.add_argument('--align', type = str, required = True)

args = parser.parse_args()

align_flag = args.align
if align_flag == 'False':
	print ""
	print "####### NO ALIGNMENT!!!!"
	print ""
	print "########################"
	print "########################"
# Parameters ######

repo_dir = '/storage/nmmsv/str-expansions/'
base_dir = '/storage/nmmsv/expansion-experiments/'
ref_genome = '/storage/resources/dbase/human/hs37d5/hs37d5.fa'

diploid = 'False'

###################
locus_name = 'CACNA1A'
exp_number = 9

nCopy = 100

coverage = 60

dist_mean  = 500
dist_sdev  = 50

copy_list = [nCopy] * 10

exp_name = 'rpt_' + locus_name + '_' + str(exp_number) + '_nC' + str(nCopy) + '_cov' + str(coverage) + '_dist' + str(dist_mean)
###################

locus = repo_dir + '/loci/'+locus_name+'.bed'
motif, str_len = find_motif_refAll(locus)
ref_allele = int(str_len / len(motif))
flank_len = 3000
base_error = 0.0

read_len = 100
mutat_rate = 0.0
indel_frac = 0.0
indel_xtnd = 0.0


num_threads = 5
bam_filter = True
heat_map_limit = 10
###################


# StackOverflow
def mkdir_p(path):
    try:
        os.makedirs(path)
        print 'Created path: ', path
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

### Creating Directories ###
print '# Creating new directories..'
exp_dir = base_dir + exp_name + '/'
sim_gen_dir = exp_dir + '/simulated_genome/'
sim_read_dir = exp_dir + '/simulated_read/'
algn_read_dir = exp_dir + '/aligned_read/'
estm_dir = exp_dir + '/estimation/'
plot_dir = exp_dir + '/plots/'
temp_dir = exp_dir + '/temp/'
mkdir_p(base_dir)
mkdir_p(exp_dir)
mkdir_p(sim_gen_dir)
mkdir_p(sim_read_dir)
mkdir_p(algn_read_dir)
mkdir_p(estm_dir)
mkdir_p(plot_dir)
mkdir_p(temp_dir)
############################


### STEP 0: Create Profile #####
if align_flag == 'True':
	subprocess.call([	'python', 			repo_dir + '0_create_profile.py', \
						'--exp-name',		exp_name, \
						'--locus', 			locus, \
						'--motif',			motif, \
						'--flank-len',		str(flank_len), \
						'--ref-gen-dir', 	ref_genome, \
						'--repo-dir',		repo_dir, \
						'--exp-dir',		exp_dir, \
						'--read-len',		str(read_len), \
						'--coverage',		str(coverage), \
						'--read-ins-mean',	str(dist_mean), \
						'--read-ins-stddev',str(dist_sdev), \
						'--num-copy'] +		[str(nc) for nc in copy_list] + \
						['--base-error',		str(base_error), \
						'--num-threads',	str(num_threads), \
						'--bam-filter', 	str(bam_filter), \
						'--ref-allele-count',str(ref_allele), \
						'--heat-map-limit', str(heat_map_limit)])
################################


### STEP 1: Simulated Genome ###
j = 0
if align_flag == 'True':
	for nc in copy_list:
		out_path = sim_gen_dir + str(j) + 'nc_' + str(nc) + '.fa'
		subprocess.call(['python', 		repo_dir + '1.2_simulate_alt_genome_core.py', \
						'--ref-genome', '/storage/resources/dbase/human/hs37d5/hs37d5.fa', \
						'--exp-name', 	exp_name, \
						'--out', 		out_path, \
						'--locus-bed',	locus, \
						'--motif',		motif, \
						'--flank-len', 	str(flank_len), \
						'--temp-dir', 	temp_dir, \
						'--num-copy',	str(nc) ,\
						'--diploid', 	diploid])
		j = j + 1

#############################

### STEP 2: wgsim ###########
j = 0
if align_flag == 'True':
	for nc in copy_list:
		in_path = sim_gen_dir + str(j) + 'nc_' + str(nc) + '.fa'
		out_pref= sim_read_dir + str(j) + 'nc_' + str(nc)
		subprocess.call(['python', 		repo_dir + '2.2_read_simulated_data_core.py', \
						'--exp-name', 	exp_name, \
						'--fasta-in',	in_path, \
						'--out-pref', 	out_pref, \
						'--coverage',	str(coverage), \
						'--num-copy',	str(nc), \
						'--dist-mean', 	str(dist_mean), \
						'--dist-sdev', 	str(dist_sdev), \
						'--motif',		motif, \
						'--base-error',	str(base_error), \
						'--flank-len', 	str(flank_len), \
						'--read-len',	str(read_len), \
						'--mutat-rate',	str(mutat_rate), \
						'--indel-frac', str(indel_frac), \
						'--indel-xtnd', str(indel_xtnd)])
		j = j + 1

#############################

### STEP 3: Alignment #######
j = 0
if align_flag == 'True':
	for nc in copy_list:
		read_grp_header = 	'\'@RG\\tID:' + exp_name + \
							'\\tSM:' + str(nc) + \
							'\\tLB:' + str(coverage)+ \
							'\\tPL:' + str(base_error) + '\''
		in_pref = sim_read_dir + str(j) + 'nc_' + str(nc)
		out_pref = algn_read_dir + str(j) + 'nc_' + str(nc)
		subprocess.call(['python', 		repo_dir + '3.2_align_read_core.py', \
						'--ref-genome', '/storage/resources/dbase/human/hs37d5/hs37d5.fa', \
						'--out-pref', 	out_pref, \
						'--in-pref', 	in_pref, \
						'--read-grp',	read_grp_header, \
						'--num-threads',str(num_threads)])
		j = j + 1

##############################


### STEP 5: Filter: Find Spanning Read Pairs #######
j = 0
for nc in copy_list:
	in_pref = algn_read_dir + str(j) + 'nc_' + str(nc)
	out_pref = algn_read_dir + str(j) + 'nc_' + str(nc) + '_srp'
	subprocess.call(['python', 		repo_dir + '5.2_filter_spanning_only_core.py', \
					'--out-pref', 	out_pref, \
					'--in-pref', 	in_pref, \
					'--exp-dir',	exp_dir ])
	j = j + 1

##################################################################

### STEP 5: Filter: Find Enclosing Reads #######
j = 0
for nc in copy_list:
	in_pref = algn_read_dir + str(j) + 'nc_' + str(nc)
	out_pref = algn_read_dir + str(j) + 'nc_' + str(nc) + '_er'
	subprocess.call(['python', 		repo_dir + '5.2_filter_enclosing_only_core.py', \
					'--out-pref', 	out_pref, \
					'--in-pref', 	in_pref, \
					'--exp-dir',	exp_dir ])
	j = j + 1

#################################################################

### STEP 5: Filter: Find Fully Repetitive Reads #######
j = 0
for nc in copy_list:
	in_pref = algn_read_dir + str(j) + 'nc_' + str(nc)
	out_pref = algn_read_dir + str(j) + 'nc_' + str(nc) + '_frr'
	subprocess.call(['python', 		repo_dir + '5.2_filter_FRR_only_core.py', \
					'--out-pref', 	out_pref, \
					'--in-pref', 	in_pref, \
					'--exp-dir',	exp_dir ])
	j = j + 1





