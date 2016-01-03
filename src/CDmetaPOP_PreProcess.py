# -------------------------------------------------------------------------------------------------
# CDmetaPOP_PreProcess.py
# Author: Erin L Landguth
# Created: October 2010
# Description: This is the function/module file pre processing.
# --------------------------------------------------------------------------------------------------

# Import Modules with Except/Try statements

# Numpy functions
try:
	import numpy as np 
	from numpy.random import *
except ImportError:
	raise ImportError, "Numpy required."

# Scipy function KDTree
try:
	from scipy.spatial import KDTree
	scipyAvail = True
except ImportError:
	raise ImportError, "Scipy required."
	scipyAvail = False
from scipy.stats import truncnorm
from scipy.linalg import eigh, cholesky
from scipy.stats import norm
	
# CDPOP functions
try:
	from CDmetaPOP_Mate import *
	from CDmetaPOP_Offspring import *
	from CDmetaPOP_Mortality import *
	from CDmetaPOP_Immigration import *
	from CDmetaPOP_Emigration import *
	#
except ImportError:
	raise ImportError, "CDmetaPOP Modules missing."
	
# General python imports
import os,sys
from ast import literal_eval 

# ---------------------------------------------------------------------------------------------------
def count_unique(keys):
    uniq_keys = np.unique(keys)
    bins = uniq_keys.searchsorted(keys)
    return uniq_keys, np.bincount(bins)
	#End::count_unique()

# ---------------------------------------------------------------------------------------------------	 
def w_choice_general(lst):
	'''
	w_choice_general()
	Weighted random draw from a list, probilities do not have to add to one.
	'''
	wtotal=sum(x[1] for x in lst)
	n=random.uniform(0,wtotal)
	count = 0
	for item, weight in lst:
		if n < weight:
			break
		n = n-weight
		count = count + 1
	# The case where all of the values in lst are the same
	if len(lst) == count:
		count = count-1
	return item,count
	#End::w_choice_general()		
	
# ----------------------------------------------------------------------------------
def loadFile(filename, header_lines=0, delimiter=None, cdpop_inputvars=False): ###
	'''
	Used to load file hearders according to current UNICOR standards
	as of 5/19/2011
	'''
	try:
		inputfile = open(filename)
	except (IOError,OSError) as e:
		print("Load file: %s the file (%s) is not available!"%(e,filename))
		sys.exit(-1)
	header_dict = {}
	data_list = []
	index_list = [] ###
	
	if delimiter != None:
		lines = [ln.rstrip().split(delimiter) for ln in inputfile]
	else:
		lines = [ln.rstrip().split() for ln in inputfile]
	# Close file
	inputfile.close()
		
	for i,line in enumerate(lines):
		if i < header_lines:
			if len(line) <= 1:
				print("Only one header value in line, skipping line...")
				continue
			#else:	
			elif len(line) == 2: ###
				header_dict[line[0]] = line[1]
			### working with a file where the first line is all header keys
			### and the following lines are their data
			elif cdpop_inputvars: ###
				for j in range(len(line)): ###
					header_dict[line[j]] = [] ###
					index_list.append(line[j]) ###
		else:
			#This is a fix to remove empty entries from from a line if they
			#exist, this is to fix a problem with reading in cdmatrices
			
			for i in range(line.count('')):
				line.remove('')
			data_list.append(line)
			if cdpop_inputvars: ###
				#tempTuple = ()
				for j in range(len(line)): ###
					# remove the following lines should the tuple representing bar-delimited values break anything -TJJ
					if line[j].find('|') != -1:
						tempList = line[j].split('|')
						line[j] = tuple(tempList)
					#---
					
					header_dict[index_list[j]].append(line[j]) ###
	
	if not cdpop_inputvars:
		return header_dict, data_list
	else:
		n_jobs = len(lines) - header_lines
		return header_dict, index_list, n_jobs
	#End::loadFile
	
# ---------------------------------------------------------------------------------------------------	 
def GetMaxCDValue(threshold,cdmatrix):	
	'''
	GetMaxCDValue()
	This function calculates the maximum movement thresholds.
	'''	
	
	# movement threshold if max specified
	if str(threshold).endswith('max'):
		# If max
		if len(threshold.strip('max')) == 0:
			threshold = np.amax(cdmatrix)
		else:
			threshold = (float(threshold.strip('max'))/100.)\
			*np.amax(cdmatrix)
	else:
		threshold = float(threshold)
	
	return threshold
	#End::GetMaxCDValue()
	
# ---------------------------------------------------------------------------------------------------	 
def ReadCDMatrix(cdmatrixfilename,function,threshold,A,B,C):
	'''
	ReadMateCDMatrix()
	This function reads in the mating cost distance matrix.
	'''	
	
	# Check statements
	if os.path.exists(cdmatrixfilename):
		# Open file for reading
		inputfile = open(cdmatrixfilename,'rU')
	else:
		print("CDmetaPOP ReadCDMatrix() error: open failed, could not open %s"%(cdmatrixfilename))
		sys.exit(-1)
	
	# Read lines from the file
	lines = inputfile.readlines()
	
	# Close the file
	inputfile.close()
	
	# Create an empty matrix to append to 
	bigCD = []
	
	# Split up each line in file and append to empty matrix, x
	for spot in lines:
		thisline = spot.strip('\n').split(',')
		bigCD.append(thisline[0:len(lines)])
	bigCD = np.asarray(bigCD,dtype='float')
	
	# Delete lines from earlier
	del(lines)
		
	# Store number of files
	nofiles = len(bigCD)
	
	# Calculate max and min of bigCD matrix
	minbigCD = np.amin(bigCD)
	maxbigCD = np.amax(bigCD)
	
	# Get maximum cdvalue to use for movethreshold if specified
	threshold = GetMaxCDValue(threshold,bigCD)
	
	# Create a matrix of to be filled 
	cdmatrix = []
	if function != '9':
		# Fill up matrix with float value of array x
		for j in xrange(nofiles):
			cdmatrix.append([])
			for k in xrange(nofiles):
				
				# For the linear function
				if function == '1':
					scale_min = 0.
					scale_max = threshold
					# Set = to 0 if cdvalue is greater than movethreshold
					if float(bigCD[j][k]) > threshold:
						cdmatrix[j].append(0.0)
					# If threshold is 0 (philopatry) set to 1 - can't dived by 0
					elif float(bigCD[j][k]) <= threshold and threshold == 0.0:
						cdmatrix[j].append(1.0)
					# Else calculated function value and if not philopatry
					elif float(bigCD[j][k]) <= threshold and threshold != 0.0:
						cdmatrix[j].append(-(1./threshold)*float(bigCD[j][k]) + 1)
					else:
						print('Something off in linear function values.')
						sys.exit(-1)
							
				# For the inverse square function
				elif function == '2':			
					# This function gets rescale: calculate here
					if threshold == 0:
						scale_min = 0.
					else:
						scale_min = 1./(pow(threshold,2))
					scale_max = 1.
					
					# Set = to 0 if cdvalue is greater than movethreshold
					if float(bigCD[j][k]) > threshold:
						cdmatrix[j].append(0.0)
					# If threshold is 0 (philopatry) set to 1 - can't dived by 0
					elif float(bigCD[j][k]) <= threshold and threshold == 0.0:
						cdmatrix[j].append(1.0)
					# If cd mat is 0. 
					elif float(bigCD[j][k]) <= threshold and threshold != 0.0 and float(bigCD[j][k]) == 0.0 or (minbigCD == maxbigCD or int(maxbigCD) == 0):
						cdmatrix[j].append(1.0)
					# Else calculated function value
					elif float(bigCD[j][k]) <= threshold and threshold != 0.0 and float(bigCD[j][k]) != 0.0 and (minbigCD != maxbigCD and int(maxbigCD) != 0):
						invsq_val = 1./(pow(float(bigCD[j][k]),2))
						invsq_val = (invsq_val - scale_min) / (scale_max - scale_min)
						cdmatrix[j].append(invsq_val)# Else something else.
					else:
						print('Something off in inv squ function values.')
						sys.exit(-1)
						
				# Nearest neighbor function here
				elif function == '3':
					print('Nearest neighbor function is not currently implemented.')
					print('You can use Linear function with neighbor threshold for approximation. Email Erin.')
					sys.exit(-1)
				
				# Random function here
				elif function == '4':
					scale_min = 0.
					scale_max = threshold
					# Set = to 0 if cdvalue is greater than movethreshold
					if float(bigCD[j][k]) > threshold:
						cdmatrix[j].append(0.0)
					# Else calculated function value
					else:
						cdmatrix[j].append(1.0)
				
				# For the negative binomial function
				elif function == '5':
					
					# This function gets rescale: calculate here
					scale_min = A*pow(10,-B*float(threshold))
					scale_max = A*pow(10,-B*float(minbigCD))
				
					# Set = to 0 if cdvalue is greater than movethreshold
					if float(bigCD[j][k]) > threshold:
						cdmatrix[j].append(0.0)
					# Rescaled value divide by zero check cases
					elif float(bigCD[j][k]) <= threshold and threshold == 0.0 and (minbigCD == maxbigCD or int(maxbigCD) == 0):
						cdmatrix[j].append(1.0)
					# Else calculated function value
					elif float(bigCD[j][k]) <= threshold and threshold != 0.0 and (minbigCD != maxbigCD and int(maxbigCD) != 0):
						negexp = A*pow(10,-B*float(bigCD[j][k]))
						negexp = (negexp - scale_min) / (scale_max - scale_min)
						cdmatrix[j].append(negexp)
					# Else something else.
					else:
						print('Something off in neg exp function values.')
						sys.exit(-1)
						
				# For in a subpopulation only
				elif function == '6':
					scale_min = 0.
					scale_max = 1.
					# Check if within the same subpopulation
					if j == k:					
						cdmatrix[j].append(1.0)
					else:
						cdmatrix[j].append(0.0)
				
				# For Gaussian function 
				elif function == '7':
				
					# This function gets rescale: calculate here
					scale_min = A*np.exp(-((float(threshold)-B)**2)/(2*C**2))
					scale_max = A*np.exp(-((float(minbigCD)-B)**2)/(2*C**2))
				
					# Set = to 0 if cdvalue is greater than movethreshold
					if float(bigCD[j][k]) > threshold:
						cdmatrix[j].append(0.0)
					# Rescaled value divide by zero check cases
					elif float(bigCD[j][k]) <= threshold and threshold == 0.0 and (minbigCD == maxbigCD or int(maxbigCD) == 0):
						cdmatrix[j].append(1.0)
					# Else calculated function value
					elif float(bigCD[j][k]) <= threshold and threshold != 0.0 and (minbigCD != maxbigCD and int(maxbigCD) != 0):
						gauss_val = A*np.exp(-((float(bigCD[j][k])-B)**2)/(2*C**2))
						gauss_val = (gauss_val - scale_min) / (scale_max - scale_min)
						cdmatrix[j].append(gauss_val)
					# Else something else.
					else:
						print('Something off in gauss function values.')
						sys.exit(-1)
						
				# For cost distance matrix only function 
				elif function == '8':
				
					scale_min = minbigCD
					scale_max = threshold
					
					# Set = to 0 if cdvalue is greater than movethreshold
					if float(bigCD[j][k]) > threshold:
						cdmatrix[j].append(0.0) 
					# Rescaled value divide by zero check cases - philopatry
					elif (float(bigCD[j][k]) <= threshold and threshold == 0.0) and (minbigCD == maxbigCD or int(maxbigCD) == 0 or threshold == minbigCD):
						cdmatrix[j].append(1.0)
					# If cd mat is 0. 
					elif (float(bigCD[j][k]) <= threshold and threshold != 0.0 and float(bigCD[j][k]) == 0.0) or (minbigCD == maxbigCD or int(maxbigCD) == 0 or threshold == minbigCD):
						cdmatrix[j].append(1.0)
					# Else calculated function value
					elif (float(bigCD[j][k]) <= threshold and threshold != 0.0 and float(bigCD[j][k]) != 0.0) and (minbigCD != maxbigCD and int(maxbigCD) != 0 and threshold != minbigCD):
						cd_val = (float(bigCD[j][k]) - scale_min) / (scale_max - scale_min)
						cdmatrix[j].append(1. - cd_val)
					# Else something else.
					else:
						print('Something off in 8 function values.')
						sys.exit(-1)
						
				# error
				else:
					print('This movement function option does not exist.')
					sys.exit(-1)
	else: # For option 9
		cdmatrix = bigCD
		scale_min = 0.0
		scale_max = 1.0
		
	# Transpose all matrices here (this was because gdistance asymetrical matrices read by column
	cdmatrix = np.transpose(np.asarray(cdmatrix))
	
	# Delete variables
	del(bigCD)
		
	# Return variables
	tupReadMat = cdmatrix,threshold,scale_min,scale_max
	return tupReadMat
	#End::ReadMateCDMatrix
	
# ---------------------------------------------------------------------------------------------------	
def CreateAlleleList(loci,alleles,xgenes):
	'''
	CreateAlleleList()
	This function creates a list for the allele storage.
	'''		
	
	# Store all information in a list [loci][allele#,probability]
	allelst = []
	for i in xrange(loci):
		allelst.append([])
		for k in xrange(alleles[i]):
			allelst[i].append([int(k),float(xgenes[alleles[i]*i+1+k][1])])
	
	# Return variables
	return allelst
	#End::CreateAlleleList()
	
# ---------------------------------------------------------------------------------------------------	 
def InitializeGenes(datadir,allefreqfilename,loci,alleles):	
	
	'''
	InitializeGenes()	
	'''
	
	allelst = []
	# Loop through allelefrequency files
	for ifile in xrange(len(allefreqfilename)):
		
		fileans = allefreqfilename[ifile]
		
		# If genetic structure intialized by a file...
		if fileans != 'random':
			
			# Check statements
			if os.path.exists(datadir+fileans):
				# Open file for reading
				inputfile = open(datadir+fileans,'rU')
			else:
				print("CDmetaPOP InitializeGenes() error: open failed, could not open %s"%(fileans))
				sys.exit(-1)
				
			# Read lines from the file
			lines = inputfile.readlines()
			
			#Close the file
			inputfile.close()
			
			# Create an empty matrix to append to
			xgenes = []
			
			# Split up each line in file and append to empty matrix, x
			for i in lines:
				thisline = i.strip('\n').strip('\r').strip(' ').split(',')
				xgenes.append(thisline)
			
			# Error check here
			if (len(xgenes)-1) != sum(alleles):
				print('Allele frequency file is not the specified number of loci and alleles as in in input file.')
				sys.exit(-1)
			
			# Delete lines from earlier
			del(lines)
			
			# Call CreateAlleleList()
			allelst.append(CreateAlleleList(loci,alleles,xgenes))
		
		# If genetic structure is to be initialize by random
		elif fileans == 'random':
			
			# Create even distribution
			xgenes = []
			xgenes.append(['Allele List','Frequency'])
			for iloci in xrange(loci):
				for iall in xrange(alleles[iloci]):
					xgenes.append(['L'+str(iloci)+'A'+str(iall),str(1.0/alleles[iloci])])
			
			# Call CreateAlleleList()
			allelst.append(CreateAlleleList(loci,alleles,xgenes))
		
	# Delete x variable
	del(xgenes)
	
	# Return variables
	return allelst
	#End::InitializeGenes()
	
# ---------------------------------------------------------------------------------------------------	 
def InitializeAge(K,agefilename,datadir):
	'''
	InitializeAge()
	This function initializes the age of each population
	with an age distribution list.
	'''
	
	# Store all information in a list [age,probability]
	agelst = [] # [age,probability] for age distribution
	ageclass = []
	ageno = []
	Femalepercent = []
	age_percmort_out = []
	age_percmort_back = []
	size_percmort_out = []
	size_percmort_back = []
	age_percmort_out_sd = []
	age_percmort_back_sd = []
	size_percmort_out_sd = []
	size_percmort_back_sd = []
	age_Mg = []
	age_S = []
	age_mu = []
	age_size_mean = []
	age_size_std = []
	M_mature = []
	F_mature = []
	age_sigma = []
	age_cap_out = []
	age_cap_back = []
	
	lencheck = []
	
	# Then loop through each file
	for isub in xrange(len(K)):
		
		# Check statements
		if os.path.exists(datadir+agefilename[isub]):
			# Open file for reading
			inputfile = open(datadir+agefilename[isub],'rU')
		else:
			print("CDmetaPOP InitializeAge() error: open failed, could not open %s"%(datadir+agefilename[isub]))
			sys.exit(-1)
		
		# Read lines from the file
		lines = inputfile.readlines()
		
		#Close the file
		inputfile.close()
		
		# Create an empty matrix to append to
		xage = []

		# Split up each line in file and append to empty matrix, x
		for i in lines:
			thisline = i.strip('\n').strip('\r').strip(' ').split('\r')
			for j in xrange(len(thisline)):
				xage.append(thisline[j].split(','))
		lencheck.append(len(xage)-1)	
		# Delete lines from earlier
		del(lines)
		
		# Store all information in a list [age,probability]
		agelst.append([]) # [age,probability] for age distribution
		ageclass.append([])
		ageno.append([])
		Femalepercent.append([])
		age_percmort_out.append([])
		age_percmort_back.append([])
		size_percmort_out.append([])
		size_percmort_back.append([])
		age_percmort_out_sd.append([])
		age_percmort_back_sd.append([])
		size_percmort_out_sd.append([])
		size_percmort_back_sd.append([])
		age_Mg.append([])
		age_S.append([])
		age_mu.append([])
		age_size_mean.append([])
		age_size_std.append([])
		M_mature.append([])
		F_mature.append([])
		age_sigma.append([])
		age_cap_out.append([])
		age_cap_back.append([])
		for i in xrange(len(xage)-1):	
			ageclass[isub].append(int(xage[i+1][0]))
			age_size_mean[isub].append(float(xage[i+1][1]))
			age_size_std[isub].append(float(xage[i+1][2]))
			ageno[isub].append(float(xage[i+1][3]))
			Femalepercent[isub].append(xage[i+1][4])
			age_percmort_out[isub].append(xage[i+1][5])
			age_percmort_back[isub].append(xage[i+1][7])
			size_percmort_out[isub].append(xage[i+1][9])
			size_percmort_back[isub].append(xage[i+1][11])
			age_percmort_out_sd[isub].append(float(xage[i+1][6]))
			age_percmort_back_sd[isub].append(float(xage[i+1][8]))
			size_percmort_out_sd[isub].append(float(xage[i+1][10]))
			size_percmort_back_sd[isub].append(float(xage[i+1][12]))
			age_Mg[isub].append(float(xage[i+1][13]))
			age_S[isub].append(float(xage[i+1][14]))
			M_mature[isub].append(float(xage[i+1][15]))
			F_mature[isub].append(float(xage[i+1][16]))
			age_mu[isub].append(float(xage[i+1][17]))
			age_sigma[isub].append(float(xage[i+1][18]))
			age_cap_out[isub].append(xage[i+1][19])
			age_cap_back[isub].append(xage[i+1][20])		
		
		# Get age distribution list
		for i in xrange(len(ageno[isub])):
			agelst[isub].append([ageclass[isub][i],ageno[isub][i]/sum(ageno[isub])])
		
		# Error checks here: if number of classes does not equal mortality age classes
		if len(agelst[isub]) != len(age_percmort_out[isub]) != len(age_percmort_back[isub]):
			print('Agedistribution data not fully entered correctly.')
			sys.exit(-1)
		# Error probabilties in age list....finish error checks
		if len(age_Mg[isub]) != len(age_S[isub]):
			print('Age distribution file in the wrong format.')
			sys.exit(-1)
		# Error check on Femalepercent
		if 'WrightFisher' in Femalepercent[isub]:
			if Femalepercent[isub][1:] != Femalepercent[isub][-1:]:
				print('Wright Fisher specified in Female Percent in Agevars.csv file. All age classes must be WrightFisher.')
				sys.exit(-1)
		
		# Deletes
		del(xage)
	
	# Error check, all patches must have the same length of classes
	if sum(lencheck) / float(len(lencheck)) != lencheck[0]:
		print('ClassVars all must have the same number of classes.')
		sys.exit(-1)
		
	# Return variables
	tupAgeFile = agelst,age_percmort_out,age_percmort_back,age_Mg,age_S,\
	Femalepercent,age_mu,age_size_mean,age_size_std,M_mature,F_mature,age_sigma,age_cap_out,age_cap_back,size_percmort_out,size_percmort_back,age_percmort_out_sd,age_percmort_back_sd,size_percmort_out_sd,size_percmort_back_sd
	
	return tupAgeFile
	#End::InitializeAge()

# ---------------------------------------------------------------------------------------------------	 
def InitializeID(K,N):
	'''
	InitializeID()
	This function initializes the location of each individuals for the id varialbe
	{Initial,Residor,Immigrant,Emigrant,Stayor}_{Year born}_{Natal Pop}_{Numeric ID}
	'''
	
	id = []
	for isub in xrange(len(K)):
		
		for iind in xrange(K[isub]):
			# See if spot fills based on Nvals
			probfill = float(N[isub]/float(K[isub]))
			randno = rand()
			if randno <= probfill:
				# Get name
				name = 'R'+str(isub+1)+'_P'+str(isub+1)+'_Y-1_'+str(iind)
				id.append(name)
			else:
				id.append('OPEN')
	
	return id
	#End::InitializeID()

# ---------------------------------------------------------------------------------------------------	 
def InitializeVars(K,id,Femalepercent,agelst,cdinfect,loci,alleles,allelst,age_size_mean,age_size_std,subpop,M_mature,F_mature,eggFreq,sizeans,Fmat_set,Mmat_set,Fmat_int,Fmat_slope,Mmat_int,Mmat_slope,cdevolveans,fitvals,burningen):
	'''
	InitializeVars()
	This function initializes the age,sex,infection,genes of each individual based for the id variable
	'''
	age = []
	sex = []
	size = []
	infection = []
	genes = []
	mature = []
	capture = []
	recapture = []
	layEggs = []
	
	# Just loop through actual individuals, else this can take a long while - carful of indexing
	id = np.asarray(id)
	index_ind = np.where(id != 'OPEN')[0] # Index location for individuals
	id_N = id[index_ind] # Cut down id
	subpop_N = np.asarray(subpop)[index_ind] # Cut subpop
	for iind in xrange(len(id_N)):
		
		# ---------------
		# Get patch number (minus 1 for indexing)
		# ----------------
		isub = int(subpop_N[iind]) - 1
		
		# --------------
		# Select the age
		# --------------
		agetemp = w_choice_general(agelst[isub])[0]
		age.append(agetemp)
		
		# ---------------------------------
		# Set Size here
		# ---------------------------------
		# Set the size - add in Todd & Ng method
		mu,sigma = age_size_mean[isub][agetemp],age_size_std[isub][agetemp]			
		# Case here for sigma == 0
		if sigma != 0:
			lower, upper = 0,np.inf
			sizesamp  = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)			
		else:
			sizesamp = mu
		size.append(sizesamp)
		
		# ------------------------------
		# Check for size control
		# ------------------------------		
		if sizeans == 'Y':
			# Get size adjusted age
			size_mean_middles = np.asarray(age_size_mean[isub])[1:] - np.diff(np.asarray(age_size_mean[isub]).astype('f'))/2
			age_adjusted = np.searchsorted(size_mean_middles, sizesamp)
		else:
			age_adjusted = agetemp
		
		# ------------------------------
		# Sex set
		# ------------------------------
		# Case for Wright Fisher or not
		if Femalepercent[isub][age_adjusted] != 'WrightFisher':
			# Select the sex
			randsex = int(100*rand())				
			# If that random number is less than Femalepercent, assign it to be a female
			if randsex < int(Femalepercent[isub][age_adjusted]):
				offsex = 0				
			# If the random number is greater than the Femalepercent, assign it to be a male
			else:
				offsex = 1					
			sex.append(offsex)
		# Special case for WrightFisher
		else: 
			offsex = int(2*rand())
			sex.append(offsex) # temporary fill
		
		# ------------------------
		# Set the infection status
		# ------------------------
		if cdinfect == 'Y':
			# Append a random number 0 or 1
			infection.append(int(2*rand()))
		else:
			infection.append(0)	
			
		# -------------------
		# Capture probability
		# -------------------
		capture.append(0)
		recapture.append(0)
		
		# --------------------------
		# Get genes - For each loci:
		# --------------------------		
		genes.append([]) # And store genes information		
		for j in xrange(loci):
							
			# Take a random draw from the w_choice function at jth locus
			rand1 = w_choice_general(allelst[isub][j])[0]
			rand2 = w_choice_general(allelst[isub][j])[0]
			
			# Store genes loci spot
			genes[iind].append([])
			
			# Append assinment onto indall array - run through each condition for assignment of 1s or 2s or 0s
			# 	1s = heterozygous at that locus
			#	2s = homozygous at that locus
			#	0s = absence of allele
			for k in xrange(alleles[j]):
									
				# Assignment of 2, the rest 0
				if rand1 == rand2: 
					if k < rand1 or k > rand1:
						tempindall = 0
					elif k == rand1:
						tempindall = 2
						
				# Assignment of 1s, the rest 0
				if rand1 != rand2:
					if k < min(rand1,rand2) or k > max(rand1,rand2):
						tempindall = 0
					elif k == rand1 or k == rand2:
						tempindall = 1
					else:
						tempindall = 0
			
				# And to genes list
				genes[iind][j].append(tempindall)
	
		# ---------------------------------------------
		# Set maturity Y or N and get egg lay last year
		# ---------------------------------------------		
		if sizeans == 'N': # Age control
			if offsex == 0: # Female
				if Fmat_set == 'N': # Use prob value
					matval = F_mature[isub][agetemp]
				else: # Use set age
					if agetemp >= int(Fmat_set): # Age check
						matval = 1.0
					else:
						matval = 0.0				
			else: # Male			
				if Mmat_set == 'N': # Use prob value
					matval = M_mature[isub][agetemp]
				else: # Use set age
					if agetemp >= int(Mmat_set): # Age check
						matval = 1.0
					else:
						matval = 0.0				
		elif sizeans == 'Y': # Size control
			if (cdevolveans == 'M' or cdevolveans == 'MG_ind' or cdevolveans == 'MG_link') and burningen <= 0: # cdevolve answer mature
				tempgenes = genes[iind]
				if tempgenes[0][0] == 2: # AA
					tempvals = fitvals[isub][0] # First spot AA
					# In case cdclimate is on, grab first split
					tempvals = tempvals.split('|')[0]
					# Then split ;
					tempvals = tempvals.split(';')
					# Then replace Fmat/Mmat values
					Fmat_int = float(tempvals[3])
					Fmat_slope = float(tempvals[2])
					Mmat_int = float(tempvals[1])
					Mmat_slope = float(tempvals[0])
				elif tempgenes[0][0] == 1 and tempgenes[0][1] == 1: # Aa
					tempvals = fitvals[isub][1] # Second spot Aa
					# In case cdclimate is on, grab first split
					tempvals = tempvals.split('|')[0]
					# Then split ;
					tempvals = tempvals.split(';')
					# Then replace Fmat/Mmat values
					Fmat_int = float(tempvals[3])
					Fmat_slope = float(tempvals[2])
					Mmat_int = float(tempvals[1])
					Mmat_slope = float(tempvals[0])
				elif tempgenes[0][1] == 2: # aa
					tempvals = fitvals[isub][2] # third spot aa
					# In case cdclimate is on, grab first split
					tempvals = tempvals.split('|')[0]
					# Then split ;
					tempvals = tempvals.split(';')
					# Then replace Fmat/Mmat values
					Fmat_int = float(tempvals[3])
					Fmat_slope = float(tempvals[2])
					Mmat_int = float(tempvals[1])
					Mmat_slope = float(tempvals[0])
				else:
					# Then replace Fmat/Mmat values
					Fmat_int = float(Fmat_int)
					Fmat_slope = float(Fmat_slope)
					Mmat_int = float(Mmat_int)
					Mmat_slope = float(Mmat_slope)				
			
			if offsex == 0: # Female
				if Fmat_set == 'N': # Use equation - size
					matval = np.exp(Fmat_int + Fmat_slope * sizesamp) / (1 + np.exp(Fmat_int + Fmat_slope * sizesamp))
				else: # Use set size
					if sizesamp >= int(Fmat_set):
						matval = 1.0
					else:
						matval = 0.0				
			else: # Male			
				if Mmat_set == 'N': # Use equation - size
					matval = np.exp(Mmat_int + Mmat_slope * sizesamp) / (1 + np.exp(Mmat_int + Mmat_slope * sizesamp))
				else: # Use set size
					if sizesamp >= int(Mmat_set):
						matval = 1.0
					else:
						matval = 0.0						
		else:
			print('Size control option not correct, N or Y.')
			sys.exit(-1)
			
		randmat = rand()
		if randmat < matval:
			mature.append(1)
			randegglay = rand()
			if randegglay < eggFreq:
				layEggs.append(1)
			else:
				layEggs.append(0)
		else:
			mature.append(0)
			layEggs.append(0)
	
	# Return Vars
	return age,sex,size,infection,genes,mature,capture,layEggs,recapture,id_N,subpop_N
	#End::InitializeVars()
	
# ---------------------------------------------------------------------------------------------------	 
def ReadXY(xyfilename):
	'''
	ReadMateXYCDMatrix()
	This function reads in the xy values for the cost distance matrix.
	'''		
	
	# Check statements
	if os.path.exists(xyfilename):
		# Open file for reading
		inputfile = open(xyfilename,'rU')
	else:
		print("CDmetaPOP ReadXY() error: open failed, could not open %s"%(xyfilename))
		sys.exit(-1)
	
	# Read lines from the file
	lines = inputfile.readlines()
	
	#Close the file
	inputfile.close()
	
	# Create an empty matrix to append to
	xy = []
	
	# Split up each line in file and append to empty matrix, x
	for i in lines:
		thisline = i.rstrip('\n').rstrip('\r').split(',')
		xy.append(thisline)
		
	# Delete lines from earlier
	del(lines)
	
	# Return variables
	return xy
	#End::ReadXY()

# ---------------------------------------------------------------------------------------------------	 
def DoCDClimate(datadir,icdtime,cdclimgentime,matecdmatfile,dispOutcdmatfile,dispBackcdmatfile,straycdmatfile,matemoveno,FdispmoveOutno,MdispmoveOutno,FdispmoveBackno,MdispmoveBackno,StrBackno,matemovethresh,FdispmoveOutthresh,MdispmoveOutthresh,FdispmoveBackthresh,MdispmoveBackthresh,StrBackthresh,matemoveparA,matemoveparB,matemoveparC,FdispmoveOutparA,FdispmoveOutparB,FdispmoveOutparC,MdispmoveOutparA,MdispmoveOutparB,MdispmoveOutparC,FdispmoveBackparA,FdispmoveBackparB,FdispmoveBackparC,MdispmoveBackparA,MdispmoveBackparB,MdispmoveBackparC,StrBackparA,StrBackparB,StrBackparC,Mg,Str,K,outsizevals,backsizevals,outgrowdays,backgrowdays,fitvals,popmort_back,popmort_out,eggmort,Kstd,popmort_back_sd,popmort_out_sd,eggmort_sd,outsizevals_sd,backsizevals_sd,outgrowdays_sd,backgrowdays_sd,pop_capture_back,pop_capture_out,cdevolveans):
	'''
	DoCDCliamte()
	Reads in cost distance matrices and converts to probabilities.
	'''
	
	# -------------------------------
	# Extract cdclimate values here
	# -------------------------------
	# Store cdmat file information - header file (loadFile()) passes tuple or string if only 1
	if not isinstance(cdclimgentime, (list,tuple)):
		# Error checks
		if cdclimgentime != ['0']:
			print('If not using CDClimate option, set begin time loop with cdclimgentime at 0.')
			sys.exit(-1)
	
	# Check for each instance
	if isinstance(matecdmatfile, (list,tuple)):
		matecdmatfile = datadir+matecdmatfile[icdtime]
	else:	
		matecdmatfile = datadir+matecdmatfile
	if isinstance(dispOutcdmatfile, (list,tuple)):
		dispOutcdmatfile = datadir+dispOutcdmatfile[icdtime]
	else:
		dispOutcdmatfile = datadir+dispOutcdmatfile
	if isinstance(dispBackcdmatfile, (list,tuple)):
		dispBackcdmatfile = datadir+dispBackcdmatfile[icdtime]
	else:
		dispBackcdmatfile = datadir+dispBackcdmatfile
	if isinstance(straycdmatfile, (list,tuple)):
		straycdmatfile = datadir+straycdmatfile[icdtime]
	else:
		straycdmatfile = datadir+straycdmatfile	
	if isinstance(matemoveno, (list,tuple)):
		matemoveno = matemoveno[icdtime]		
	if isinstance(FdispmoveOutno, (list,tuple)):
		FdispmoveOutno = FdispmoveOutno[icdtime]
	if isinstance(MdispmoveOutno, (list,tuple)):
		MdispmoveOutno = MdispmoveOutno[icdtime]
	if isinstance(FdispmoveBackno, (list,tuple)):
		FdispmoveBackno = FdispmoveBackno[icdtime]
	if isinstance(MdispmoveBackno, (list,tuple)):
		MdispmoveBackno = MdispmoveBackno[icdtime]
	if isinstance(StrBackno, (list,tuple)):
		StrBackno = StrBackno[icdtime]
	if isinstance(matemovethresh, (list,tuple)):
		matemovethresh = matemovethresh[icdtime]
	if isinstance(FdispmoveOutthresh, (list,tuple)):
		FdispmoveOutthresh = FdispmoveOutthresh[icdtime]
	if isinstance(MdispmoveOutthresh, (list,tuple)):
		MdispmoveOutthresh = MdispmoveOutthresh[icdtime]
	if isinstance(FdispmoveBackthresh, (list,tuple)):
		FdispmoveBackthresh = FdispmoveBackthresh[icdtime]
	if isinstance(MdispmoveBackthresh, (list,tuple)):
		MdispmoveBackthresh = MdispmoveBackthresh[icdtime]
	if isinstance(StrBackthresh, (list,tuple)):
		StrBackthresh = StrBackthresh[icdtime]
	if isinstance(matemoveparA, (list,tuple)):
		matemoveparA = float(matemoveparA[icdtime])
	else:
		matemoveparA = float(matemoveparA)
	if isinstance(matemoveparB, (list,tuple)):
		matemoveparB = float(matemoveparB[icdtime])
	else:
		matemoveparB = float(matemoveparB)		
	if isinstance(matemoveparC, (list,tuple)):
		matemoveparC = float(matemoveparC[icdtime])
	else:
		matemoveparC = float(matemoveparC)
	if isinstance(FdispmoveOutparA, (list,tuple)):			
		FdispmoveOutparA = float(FdispmoveOutparA[icdtime])
	else:
		FdispmoveOutparA = float(FdispmoveOutparA)
	if isinstance(FdispmoveOutparB, (list,tuple)):
		FdispmoveOutparB = float(FdispmoveOutparB[icdtime])
	else:
		FdispmoveOutparB = float(FdispmoveOutparB)		
	if isinstance(FdispmoveOutparC, (list,tuple)):
		FdispmoveOutparC = float(FdispmoveOutparC[icdtime])
	else:
		FdispmoveOutparC = float(FdispmoveOutparC)		
	if isinstance(MdispmoveOutparA, (list,tuple)):
		MdispmoveOutparA = float(MdispmoveOutparA[icdtime])
	else:
		MdispmoveOutparA = float(MdispmoveOutparA)
	if isinstance(MdispmoveOutparB, (list,tuple)):
		MdispmoveOutparB = float(MdispmoveOutparB[icdtime])
	else:
		MdispmoveOutparB = float(MdispmoveOutparB)		
	if isinstance(MdispmoveOutparC, (list,tuple)):
		MdispmoveOutparC = float(MdispmoveOutparC[icdtime])
	else:
		MdispmoveOutparC = float(MdispmoveOutparC)		
	if isinstance(FdispmoveBackparA, (list,tuple)):
		FdispmoveBackparA = float(FdispmoveBackparA[icdtime])
	else:
		FdispmoveBackparA = float(FdispmoveBackparA)
	if isinstance(FdispmoveBackparB, (list,tuple)):
		FdispmoveBackparB = float(FdispmoveBackparB[icdtime])
	else:
		FdispmoveBackparB = float(FdispmoveBackparB)		
	if isinstance(FdispmoveBackparC, (list,tuple)):
		FdispmoveBackparC = float(FdispmoveBackparC[icdtime])
	else:
		FdispmoveBackparC = float(FdispmoveBackparC)		
	if isinstance(MdispmoveBackparA, (list,tuple)):
		MdispmoveBackparA = float(MdispmoveBackparA[icdtime])
	else:
		MdispmoveBackparA = float(MdispmoveBackparA)
	if isinstance(MdispmoveBackparB, (list,tuple)):
		MdispmoveBackparB = float(MdispmoveBackparB[icdtime])
	else:
		MdispmoveBackparB = float(MdispmoveBackparB)		
	if isinstance(MdispmoveBackparC, (list,tuple)):
		MdispmoveBackparC = float(MdispmoveBackparC[icdtime])
	else:
		MdispmoveBackparC = float(MdispmoveBackparC)		
	if isinstance(StrBackparA, (list,tuple)):
		StrBackparA = float(StrBackparA[icdtime])
	else:
		StrBackparA = float(StrBackparA)
	if isinstance(StrBackparB, (list,tuple)):
		StrBackparB = float(StrBackparB[icdtime])
	else:
		StrBackparB = float(StrBackparB)		
	if isinstance(StrBackparC, (list,tuple)):
		StrBackparC = float(StrBackparC[icdtime])
	else:
		StrBackparC = float(StrBackparC)		
	# Patch based parameters
	tempStr = []
	tempMg = []
	tempoutsize = []
	tempbacksize = []
	tempoutgrow = []
	tempbackgrow = []
	tempoutsize_sd = []
	tempbacksize_sd = []
	tempoutgrow_sd = []
	tempbackgrow_sd = []
	tempfitvals = []
	tempK = []
	tempKstd = []
	temppopmort_back = []
	temppopmort_out = []
	tempeggmort = []
	temppopmort_back_sd = []
	temppopmort_out_sd = []
	tempeggmort_sd = []
	temppopCapOut = []
	temppopCapBack = []
	
	for isub in xrange(len(K)):
		if len(Str[isub].split('|')) > 1:
			tempStr.append(float(Str[isub].split('|')[icdtime]))
		else:
			tempStr.append(float(Str[isub]))
		if len(Mg[isub].split('|')) > 1:
			tempMg.append(float(Mg[isub].split('|')[icdtime]))
		else:
			tempMg.append(float(Mg[isub]))
		if len(outsizevals[isub].split('|')) > 1:
			tempoutsize.append(outsizevals[isub].split('|')[icdtime])
		else:
			tempoutsize.append(outsizevals[isub])
		if len(backsizevals[isub].split('|')) > 1:
			tempbacksize.append(backsizevals[isub].split('|')[icdtime])
		else:
			tempbacksize.append(backsizevals[isub])
		
		if len(outgrowdays[isub].split('|')) > 1:
			tempoutgrow.append(outgrowdays[isub].split('|')[icdtime])
		else:
			tempoutgrow.append(outgrowdays[isub])
		if len(backgrowdays[isub].split('|')) > 1:
			tempbackgrow.append(backgrowdays[isub].split('|')[icdtime])
		else:
			tempbackgrow.append(backgrowdays[isub])
		
		if len(outsizevals_sd[isub].split('|')) > 1:
			tempoutsize_sd.append(outsizevals_sd[isub].split('|')[icdtime])
		else:
			tempoutsize_sd.append(outsizevals_sd[isub])
		
		if len(backsizevals_sd[isub].split('|')) > 1:
			tempbacksize_sd.append(backsizevals_sd[isub].split('|')[icdtime])
		else:
			tempbacksize_sd.append(backsizevals_sd[isub])
		
		if len(outgrowdays_sd[isub].split('|')) > 1:
			tempoutgrow_sd.append(outgrowdays_sd[isub].split('|')[icdtime])
		else:
			tempoutgrow_sd.append(outgrowdays_sd[isub])
		
		if len(backgrowdays_sd[isub].split('|')) > 1:
			tempbackgrow_sd.append(backgrowdays_sd[isub].split('|')[icdtime])
		else:
			tempbackgrow_sd.append(backgrowdays_sd[isub])
		
		if len(K[isub].split('|')) > 1:
			tempK.append(int(K[isub].split('|')[icdtime]))
		else:
			tempK.append(int(K[isub]))
		
		if len(Kstd[isub].split('|')) > 1:
			tempKstd.append(int(Kstd[isub].split('|')[icdtime]))
		else:
			tempKstd.append(int(Kstd[isub]))
		
		if len(popmort_back[isub].split('|')) > 1:
			temppopmort_back.append(popmort_back[isub].split('|')[icdtime])
		else:
			temppopmort_back.append(popmort_back[isub])
		
		if len(popmort_out[isub].split('|')) > 1:
			temppopmort_out.append(popmort_out[isub].split('|')[icdtime])
		else:
			temppopmort_out.append(popmort_out[isub])
		
		if len(eggmort[isub].split('|')) > 1:
			tempeggmort.append(float(eggmort[isub].split('|')[icdtime]))
		else:
			tempeggmort.append(float(eggmort[isub]))
		if len(popmort_back_sd[isub].split('|')) > 1:
			temppopmort_back_sd.append(float(popmort_back_sd[isub].split('|')[icdtime]))
		else:
			temppopmort_back_sd.append(float(popmort_back_sd[isub]))
					
		if len(popmort_out_sd[isub].split('|')) > 1:		
			temppopmort_out_sd.append(float(popmort_out_sd[isub].split('|')[icdtime]))
		else:
			temppopmort_out_sd.append(float(popmort_out_sd[isub]))
		
		if len(eggmort_sd[isub].split('|')) > 1:
			tempeggmort_sd.append(float(eggmort_sd[isub].split('|')[icdtime]))
		else:
			tempeggmort_sd.append(float(eggmort_sd[isub]))
		
		if len(pop_capture_back[isub].split('|')) > 1:
			temppopCapBack.append(pop_capture_back[isub].split('|')[icdtime])
		else:
			temppopCapBack.append(pop_capture_back[isub])
			
		if len(pop_capture_out[isub].split('|')) > 1:		
			temppopCapOut.append(pop_capture_out[isub].split('|')[icdtime])
		else:
			temppopCapOut.append(pop_capture_out[isub])			
		
		if len(fitvals) > 0:
			tempfitvals.append([])
			for i in xrange(len(fitvals[isub])):
				if cdevolveans == '1' or cdevolveans == '2' or cdevolveans == '1_mat' or cdevolveans == '2_mat':
					if len(fitvals[isub][i].split('|')) > 1:
						tempfitvals[isub].append(fitvals[isub][i].split('|')[icdtime])
					else:
						tempfitvals[isub].append(fitvals[isub][i])
				else: # For other options option in which parameters split by ;
					if len(fitvals[isub][i].split('|')) > 1:
						tempfitvals[isub].append(fitvals[isub][i].split('|')[icdtime].split(';'))
					else:
						tempfitvals[isub].append(fitvals[isub][i].split(';'))	
			# Error checks
			if cdevolveans == 'M' or cdevolveans == 'MG_ind' or cdevolveans == 'MG_link':
				if len(tempfitvals[isub][0]) != 4 or len(tempfitvals[isub][1]) != 4 or len(tempfitvals[isub][2]) != 4:
					print('CDEVOLVE answer is M, 4 parameter values must be entered for size maturation curves, see user manual.')
					sys.exit(-1)
			if cdevolveans == 'G':
				if len(tempfitvals[isub][0]) != 6 or len(tempfitvals[isub][1]) != 6 or len(tempfitvals[isub][2]) != 6:
					print('CDEVOLVE answer is G, 5 parameter values must be entered for growth equation, see user manual.')
					sys.exit(-1)
			if cdevolveans == 'MG_ind' or cdevolveans == 'MG_link':
				if len(tempfitvals[isub][3]) != 6 or len(tempfitvals[isub][4]) != 6 or len(tempfitvals[isub][5]) != 6:
					print('CDEVOLVE answer is G, 5 parameter values must be entered for growth equation, see user manual.')
					sys.exit(-1)					
		# Error check on grow days, must be equal to 365 if both entered
		if tempoutsize[isub] != 'N' and tempbacksize[isub] != 'N':
			if float(tempoutgrow[isub]) + float(tempbackgrow[isub]) > 365.:
				print('Grow days back and out must be <= 365.')
				sys.exit(-1)
		
	# ---------------------------------------------------------
	# Read in cdmatrix.csv and convert to a probability matrix
	# ---------------------------------------------------------
	
	# If mate and disp are the same, then only read in once.
	if (matecdmatfile == dispOutcdmatfile == dispBackcdmatfile == straycdmatfile) \
	and (FdispmoveOutno == MdispmoveOutno == matemoveno == FdispmoveBackno == MdispmoveBackno == StrBackno) \
	and (FdispmoveOutthresh == MdispmoveOutthresh == matemovethresh == FdispmoveBackthresh == MdispmoveBackthresh == StrBackthresh):
		tupReadMat = ReadCDMatrix(matecdmatfile,matemoveno,\
		matemovethresh,matemoveparA,matemoveparB,matemoveparC)
		
		# Unpack tuple
		matecdmatrix = np.asarray(tupReadMat[0])
		matemovethresh = tupReadMat[1]
		mate_ScaleMin = tupReadMat[2]
		mate_ScaleMax = tupReadMat[3]
		
		# Then Set disp = mate
		FdispOutcdmatrix = matecdmatrix
		MdispOutcdmatrix = matecdmatrix
		FdispmoveOutthresh = matemovethresh
		MdispmoveOutthresh = matemovethresh
		FdispBackcdmatrix = matecdmatrix
		MdispBackcdmatrix = matecdmatrix
		FdispmoveBackthresh = matemovethresh
		MdispmoveBackthresh = matemovethresh
		StrBackcdmatrix = matecdmatrix
		StrBackthresh = matemovethresh
		Str_ScaleMin = mate_ScaleMin
		Str_ScaleMax = mate_ScaleMax
		FdispBack_ScaleMin = mate_ScaleMin
		FdispBack_ScaleMax = mate_ScaleMax
		MdispBack_ScaleMin = mate_ScaleMin
		MdispBack_ScaleMax = mate_ScaleMax
		FdispOut_ScaleMin = mate_ScaleMin
		FdispOut_ScaleMax = mate_ScaleMax
		MdispOut_ScaleMin = mate_ScaleMin
		MdispOut_ScaleMax = mate_ScaleMax		

	# Else if anything is different	
	else: 
		# ---------------------------------------
		# Read in cdmatrix.csv - For Mating
		# ---------------------------------------	
		tupReadMat = ReadCDMatrix(matecdmatfile,matemoveno,\
		matemovethresh,matemoveparA,matemoveparB,matemoveparC)
		matecdmatrix = np.asarray(tupReadMat[0])
		matemovethresh = tupReadMat[1]
		mate_ScaleMin = tupReadMat[2]
		mate_ScaleMax = tupReadMat[3]
	
		# ------------------------------------------------
		# Read in cdmatrix.csv - For Female Dispersal Out
		# ------------------------------------------------	
		tupReadMat = ReadCDMatrix(dispOutcdmatfile,FdispmoveOutno,\
		FdispmoveOutthresh,FdispmoveOutparA,FdispmoveOutparB,FdispmoveOutparC)
		FdispOutcdmatrix = np.asarray(tupReadMat[0])
		FdispmoveOutthresh = tupReadMat[1]
		FdispOut_ScaleMin = tupReadMat[2]
		FdispOut_ScaleMax = tupReadMat[3]

		# ----------------------------------------------
		# Read in cdmatrix.csv - For Male Dispersal Out
		# ----------------------------------------------	
		tupReadMat = ReadCDMatrix(dispOutcdmatfile,MdispmoveOutno,\
		MdispmoveOutthresh,MdispmoveOutparA,MdispmoveOutparB,MdispmoveOutparC)
		MdispOutcdmatrix = np.asarray(tupReadMat[0])
		MdispmoveOutthresh = tupReadMat[1]
		MdispOut_ScaleMin = tupReadMat[2]
		MdispOut_ScaleMax = tupReadMat[3]
		
		# ------------------------------------------------
		# Read in cdmatrix.csv - For Female Dispersal Back
		# ------------------------------------------------	
		tupReadMat = ReadCDMatrix(dispBackcdmatfile,FdispmoveBackno,\
		FdispmoveBackthresh,FdispmoveBackparA,FdispmoveBackparB,FdispmoveBackparC)
		FdispBackcdmatrix = np.asarray(tupReadMat[0])
		FdispmoveBackthresh = tupReadMat[1]
		FdispBack_ScaleMin = tupReadMat[2]
		FdispBack_ScaleMax = tupReadMat[3]

		# ----------------------------------------------
		# Read in cdmatrix.csv - For Male Dispersal Back
		# ----------------------------------------------	
		tupReadMat = ReadCDMatrix(dispBackcdmatfile,MdispmoveBackno,\
		MdispmoveBackthresh,MdispmoveBackparA,MdispmoveBackparB,MdispmoveBackparC)
		MdispBackcdmatrix = np.asarray(tupReadMat[0])
		MdispmoveBackthresh = tupReadMat[1]
		MdispBack_ScaleMin = tupReadMat[2]
		MdispBack_ScaleMax = tupReadMat[3]
	
		# --------------------------------------------------------------
		# Read in cdmatrix.csv - For Straying back (immigration process)
		# --------------------------------------------------------------	
		tupReadMat = ReadCDMatrix(straycdmatfile,StrBackno,\
		StrBackthresh,StrBackparA,StrBackparB,StrBackparC)
		StrBackcdmatrix = np.asarray(tupReadMat[0])
		StrBackthresh = tupReadMat[1]
		Str_ScaleMin = tupReadMat[2]
		Str_ScaleMax = tupReadMat[3]
	
	# Return this functions variables
	tupClimate = matecdmatrix,FdispOutcdmatrix,MdispOutcdmatrix,FdispBackcdmatrix,MdispBackcdmatrix,\
	StrBackcdmatrix,matemovethresh,\
	FdispmoveOutthresh,MdispmoveOutthresh,\
	FdispmoveBackthresh,MdispmoveBackthresh,StrBackthresh,tempMg,tempStr,Str_ScaleMin,Str_ScaleMax,FdispBack_ScaleMin,FdispBack_ScaleMax,MdispBack_ScaleMin,MdispBack_ScaleMax,FdispOut_ScaleMin,FdispOut_ScaleMax,MdispOut_ScaleMin,MdispOut_ScaleMax,mate_ScaleMin,mate_ScaleMax,tempoutsize,tempbacksize,tempoutgrow,tempbackgrow,tempfitvals,tempK,temppopmort_back,temppopmort_out,tempeggmort,tempKstd,temppopmort_back_sd,temppopmort_out_sd,tempeggmort_sd,tempoutsize_sd,tempbacksize_sd,tempoutgrow_sd,tempbackgrow_sd,temppopCapBack,temppopCapOut,matemoveno,FdispmoveOutno,MdispmoveOutno,FdispmoveBackno,MdispmoveBackno,StrBackno 	
	return tupClimate
	#End::DoCDClimate()

# ---------------------------------------------------------------------------------------------------	
def DoStochasticUpdate(K_mu,K_std,popmort_back_mu,popmort_back_sd,popmort_out_mu,popmort_out_sd,eggmort_mu,eggmort_sd,outsizevals_mu,outsizevals_sd,backsizevals_mu,backsizevals_sd,outgrowdays_mu,outgrowdays_sd,backgrowdays_mu,backgrowdays_sd,age_percmort_out_mu,age_percmort_out_sd,age_percmort_back_mu,age_percmort_back_sd,size_percmort_out_mu,size_percmort_out_sd,size_percmort_back_mu,size_percmort_back_sd,age_percmort_back_mu_egg,age_percmort_back_sd_egg,cor_mat):	
	'''
	Here update any stochastic variables. Add in Todd and Ng method for unbias draw.
	Generate correlated deviates
	'''
	
	# --------------------------------
	# For the patch specific parameters
	# Get correlated means
	# -------------------------------
	K = []
	popmort_back = []
	popmort_out = []
	eggmort_patch = []
	outsizevals = []
	backsizevals = []
	outgrowdays = []
	backgrowdays = []
	
	# For no cor_mat answer 'N'
	if cor_mat == 'N':			
		for isub in xrange(len(K_mu)):
			# K ------------------
			mu = K_mu[isub]
			sigma = K_std[isub]
			# Case here for sigma == 0
			if sigma != 0:
				# Call a truncated normal here
				lower, upper = 0,np.inf
				X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
				K.append(int(X))
			else:
				K.append(int(mu))
			if K[isub] < 0:
				K[isub] = 0
			# mort out --------------
			mu = popmort_out_mu[isub]
			sigma = popmort_out_sd[isub]
			# If not N
			if mu == 'N' or mu == 'E':
				popmort_out.append(mu)
			else:
				mu = float(mu)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,100
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					popmort_out.append(round(X/100.,3))
				else:
					popmort_out.append(round(mu/100.,3))
				if popmort_out[isub] < 0:
					popmort_out[isub] = 0
				
			# mort back ---------------
			mu = popmort_back_mu[isub]
			sigma = popmort_back_sd[isub]
			# If not N
			if mu == 'N' or mu == 'E':
				popmort_back.append(mu)
			else:
				mu = float(mu)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,100
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					popmort_back.append(round(X/100.,3))
				else:
					popmort_back.append(round(mu/100.,3))
				if popmort_back[isub] < 0:
					popmort_back[isub] = 0
		
			# egg mort ------------------
			mu = eggmort_mu[isub]
			sigma = eggmort_sd[isub]
			# Case here for sigma == 0
			if sigma != 0:
				# Call a truncated normal here
				lower, upper = 0,100
				X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
				eggmort_patch.append(round(X/100.,3))
			else:
				eggmort_patch.append(round(mu/100.,3))
			if eggmort_patch[isub] < 0:
				eggmort_patch[isub] = 0
			# temp vals out ----------------
			mu = outsizevals_mu[isub]
			sigma = outsizevals_sd[isub]
			if mu != 'N':
				mu = float(mu)
				sigma = float(sigma)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,50
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					outsizevals.append(round(X,3))
				else:
					outsizevals.append(mu)
				if outsizevals[isub] < 0:
					outsizevals[isub] = 0
			else:
				outsizevals.append(mu)
			# temp vals back ----------------
			mu = backsizevals_mu[isub]
			sigma = backsizevals_sd[isub]
			if mu != 'N':
				mu = float(mu)
				sigma = float(sigma)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,50
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					backsizevals.append(round(X,3))
				else:
					backsizevals.append(mu)
				if backsizevals[isub] < 0:
					backsizevals[isub] = 0
			else:
				backsizevals.append(mu)
			# grow days out ----------------
			mu = outgrowdays_mu[isub]
			sigma = outgrowdays_sd[isub]
			if mu != 'N':
				mu = float(mu)
				sigma = float(sigma)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,365
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					outgrowdays.append(round(X,3))
				else:
					outgrowdays.append(mu)
				if outgrowdays[isub] < 0:
					outgrowdays[isub] = 0				
			else:
				outgrowdays.append(mu)
			# grow days back ----------------
			mu = backgrowdays_mu[isub]
			sigma = backgrowdays_sd[isub]
			if mu != 'N':
				mu = float(mu)
				sigma = float(sigma)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,365
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					backgrowdays.append(round(X,3))
				else:
					backgrowdays.append(mu)
				if backgrowdays[isub] < 0:
					backgrowdays[isub] = 0
			else:
				backgrowdays.append(mu)
	
	# If cor_mat used
	else:
		# Generate deviates, use same deviates for each patch
		# Generate 8 independent normally distributed random
		# variables (with mean 0 and std. dev. 1). Use same for each patch
		#x = norm.rvs(size=(len(cor_mat[0]), patches))?
		x = norm.rvs(size=(len(cor_mat[0]), 1))
		
		# Combine patch mu, patch sd
		patch_mu = []
		patch_mu.append(K_mu)
		patch_mu.append(popmort_out_mu)
		patch_mu.append(outsizevals_mu)
		patch_mu.append(outgrowdays_mu)
		patch_mu.append(popmort_back_mu)
		patch_mu.append(backsizevals_mu)
		patch_mu.append(backgrowdays_mu)
		patch_mu.append(eggmort_mu)
		patch_sd = []
		patch_sd.append(K_std)
		patch_sd.append(popmort_out_sd)
		patch_sd.append(outsizevals_sd)
		patch_sd.append(outgrowdays_sd)
		patch_sd.append(popmort_back_sd)
		patch_sd.append(backsizevals_sd)
		patch_sd.append(backgrowdays_sd)
		patch_sd.append(eggmort_sd)
		patch_mu = np.asarray(patch_mu)
		patch_sd = np.asarray(patch_sd,dtype = 'float')
		
		# Create covariance matrix for each patch: D*R*D
		for isub in xrange(len(K_mu)):
			D = np.diag(patch_sd[:,isub])
			
			cov_mat = np.dot(D,cor_mat)
			cov_mat = np.dot(cov_mat,D)
					
			# Get this patch values to be correlated.
			thispatch = patch_mu[:,isub]
			# Get the parameters that are 'N' or 'E'
			Nindex = np.where(thispatch == 'N')[0]
			Eindex = np.where(thispatch == 'E')[0]
			# Turn these to 0 for now and convert to array
			thispatch[Nindex] = 0.0
			thispatch[Eindex] = 0.0
			thispatch = np.asarray(thispatch,dtype = 'float')
			
			# Generate the random samples.
			y = np.random.multivariate_normal(thispatch, cov_mat, size=1)	
			
			# Clean up data - turn values back to N or E
			y = np.asarray(y,dtype='str')[0]
			y[Nindex] = 'N'
			y[Eindex] = 'E'
			
			# Then append to each variable, int, checking < 0 cases
			# K ---------------------
			K.append(int(float(y[0])))
			if K[isub] < 0:
				K[isub] = 0
			# mort out----------------
			if y[1] == 'N' or y[1] == 'E':
				popmort_out.append(y[1])
			else:
				popmort_out.append(round(float(y[1])/100.,3))
				if popmort_out[isub] < 0:
					popmort_out[isub] = 0		
			# temperautre out---------
			if y[2] == 'N':
				outsizevals.append(y[2])
			else:
				outsizevals.append(round(float(y[2]),3))
			if outsizevals[isub] < 0:
				outsizevals[isub] = 0
			# grow days out-----------
			y[3]
			if y[3] == 'N':
				outgrowdays.append(y[3])
			else:
				outgrowdays.append(round(float(y[3]),3))
			if outgrowdays[isub] < 0:
				outgrowdays[isub] = 0	
			# mort back---------------
			if y[4] == 'N' or y[4] == 'E':
				popmort_back.append(y[4])
			else:
				popmort_back.append(round(float(y[4])/100.,3))
				if popmort_back[isub] < 0:
					popmort_back[isub] = 0	
			# temperature back--------
			if y[5] == 'N':
				backsizevals.append(y[5])
			else:
				backsizevals.append(round(float(y[5]),3))
			if backsizevals[isub] < 0:
				backsizevals[isub] = 0
			# grow days back ---------
			y[6]
			if y[6] == 'N':
				backgrowdays.append(y[6])
			else:
				backgrowdays.append(round(float(y[6]),3))
			if backgrowdays[isub] < 0:
				backgrowdays[isub] = 0
			# eggmort-----------------
			y[7]
			eggmort_patch.append(round(float(y[7])/100.,3))
			if eggmort_patch[isub] < 0:
				eggmort_patch[isub] = 0
		
	# --------------------------------
	# For the age specific parameters
	# -------------------------------
	age_percmort_out = []
	age_percmort_back = []
	size_percmort_out = []
	size_percmort_back = []
	# Split up into the subpops
	for isub in xrange(len(age_percmort_back_mu)):
		age_percmort_out.append([])
		age_percmort_back.append([])
		size_percmort_out.append([])
		size_percmort_back.append([])
		for iage in xrange(len(age_percmort_back_mu[isub])):		
			# age mort back ----------------
			mu = age_percmort_back_mu[isub][iage]
			sigma = age_percmort_back_sd[isub][iage]
			if mu != 'N':
				mu = float(mu)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,100
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					age_percmort_back[isub].append(round(X/100.,3))
				else:
					age_percmort_back[isub].append(round(mu/100.,3))
				if age_percmort_back[isub][iage] < 0:
					age_percmort_back[isub][iage] = 0
			else:
				age_percmort_back[isub].append(mu)
			# age mort out ----------------
			mu = age_percmort_out_mu[isub][iage]
			sigma = age_percmort_out_sd[isub][iage]
			if mu != 'N':
				mu = float(mu)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,100
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					age_percmort_out[isub].append(round(X/100.,3))
				else:
					age_percmort_out[isub].append(round(mu/100.,3))
				if age_percmort_out[isub][iage] < 0:
					age_percmort_out[isub][iage] = 0
			else:
				age_percmort_out[isub].append(mu)
			# size mort back  ----------------
			mu = size_percmort_back_mu[isub][iage]
			sigma = size_percmort_back_sd[isub][iage]
			if mu != 'N':
				mu = float(mu)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,100
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					size_percmort_back[isub].append(round(X/100.,3))
				else:
					size_percmort_back[isub].append(round(mu/100.,3))
				if size_percmort_back[isub][iage] < 0:
					size_percmort_back[isub][iage] = 0
			else:
				size_percmort_back[isub].append(mu)
			# size mort out ----------------
			mu = size_percmort_out_mu[isub][iage]
			sigma = size_percmort_out_sd[isub][iage]
			if mu != 'N':
				mu = float(mu)
				# Case here for sigma == 0
				if sigma != 0:
					# Call a truncated normal here
					lower, upper = 0,100
					X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
					size_percmort_out[isub].append(round(X/100.,3))
				else:
					size_percmort_out[isub].append(round(mu/100.,3))
				if size_percmort_out[isub][iage] < 0:
					size_percmort_out[isub][iage] = 0
			else:
				size_percmort_out[isub].append(mu)
		
	# ----------------------------------
	# For one numbers
	# ----------------------------------
	mu = age_percmort_back_mu_egg
	sigma = age_percmort_back_sd_egg
	# Case here for sigma == 0
	if sigma != 0:
		# Call a truncated normal here
		lower, upper = 0,100
		X = truncnorm.rvs((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
		eggmort_age = round(X/100.,3)
	else:
		eggmort_age = round(mu/100.,3)	
	if eggmort_age < 0:
		eggmort_age = 0	
		
	return K,popmort_back,popmort_out,eggmort_patch,outsizevals,backsizevals,outgrowdays,backgrowdays,age_percmort_out,age_percmort_back,	size_percmort_out,size_percmort_back,eggmort_age
	#End::DoStochasticUpdate()
	
# ---------------------------------------------------------------------------------------------------	 
def DoPreProcess(outdir,datadir,ibatch,ithmcrun,xyfilename,loci,alleles,gen,logfHndl,cdevolveans,cdinfect,subpopemigration,subpopimmigration,sizeans,geneswap,eggFreq,Fmat_set,Mmat_set,Fmat_int,Fmat_slope,Mmat_int,Mmat_slope,burningen,cor_mat_ans):
	'''
	DoPreProcess()
	This function does all the pre-processing work before
	CDPOP begins its time loops.
	'''
	# ----------------------------
	# Create directory
	# ----------------------------		
	ithmcrundir = outdir+'batchrun'+\
	str(ibatch)+'mcrun'+str(ithmcrun)+'/'
	os.mkdir(ithmcrundir)
	
	# ------------------------------------------------------------------
	# Read in xy points file and store info in list
	# ------------------------------------------------------------------
	xy = ReadXY(xyfilename)

	# Error statement for column data
	if len(xy[1]) != 44:
		print('Patchvars.csv input file is not correct version, see example input files.')
		sys.exit(-1)	
		
	# Store all information in lists by variable name and store
	Pop = []
	xgridpop = []
	ygridpop = []
	K_temp = []
	Kstd_temp = []
	N0 = []	
	natal = []
	migrate = []
	allefreqfiles = []
	classvarsfiles = []
	popmort_out = []
	popmort_out_sd = []
	popmort_back = []
	popmort_back_sd = []
	Mg = []
	Str = []
	newmortperc = []
	newmortperc_sd = []
	setmigrate = []
	outsizevals = [] # growth values out
	outgrowdays = [] # grow days out
	backsizevals = [] # growth values back
	backgrowdays = [] # grow days back
	outsizevals_sd = [] # growth values out
	outgrowdays_sd = [] # grow days out
	backsizevals_sd = [] # growth values back
	backgrowdays_sd = [] # grow days back
	pop_capture_back_pass = [] # Grab first one to go into first DoUpdate
	pop_capture_out = []
	fitvals = [] # selection values
	for i in xrange(len(xy)-1):
		Pop.append(xy[i+1][0])
		xgridpop.append(float(xy[i+1][1]))
		ygridpop.append(float(xy[i+1][2]))
		K_temp.append(xy[i+1][3])
		Kstd_temp.append(xy[i+1][4])
		N0.append(int(xy[i+1][5]))
		natal.append(int(xy[i+1][6]))
		migrate.append(int(xy[i+1][7]))
		allefreqfiles.append(xy[i+1][8])
		classvarsfiles.append(xy[i+1][9])
		popmort_out.append(xy[i+1][10])
		popmort_out_sd.append(xy[i+1][11])
		popmort_back.append(xy[i+1][12])
		popmort_back_sd.append(xy[i+1][13])
		newmortperc.append(xy[i+1][14])
		newmortperc_sd.append(xy[i+1][15])
		Mg.append(xy[i+1][16])
		setmigrate.append(xy[i+1][17])
		Str.append(xy[i+1][18])	
		outsizevals.append(xy[i+1][19])
		outsizevals_sd.append(xy[i+1][20])
		outgrowdays.append(xy[i+1][21])
		outgrowdays_sd.append(xy[i+1][22])
		backsizevals.append(xy[i+1][23])
		backsizevals_sd.append(xy[i+1][24])
		backgrowdays.append(xy[i+1][25])		
		backgrowdays_sd.append(xy[i+1][26])
		pop_capture_out.append(xy[i+1][27])
		pop_capture_back_pass.append(xy[i+1][28])
		if cdevolveans == '1' or cdevolveans == 'M' or cdevolveans == '1_mat':
			fitvals.append([xy[i+1][29],xy[i+1][30],xy[i+1][31]])
		elif cdevolveans == 'G':
			fitvals.append([xy[i+1][32],xy[i+1][33],xy[i+1][34]])
		elif cdevolveans == '2' or cdevolveans == '2_mat':
			fitvals.append([xy[i+1][35],xy[i+1][36],xy[i+1][37],xy[i+1][38],xy[i+1][39],xy[i+1][40],xy[i+1][41],xy[i+1][42],xy[i+1][43]])
		elif cdevolveans == 'MG_ind' or cdevolveans == 'MG_link':
			fitvals.append([xy[i+1][29],xy[i+1][30],xy[i+1][31],xy[i+1][32],xy[i+1][33],xy[i+1][34]])
			
	# Delete x variable
	del(xy)
	
	# --------------------------------------------
	# Read in correlation matrix
	# --------------------------------------------
	if cor_mat_ans == 'N':
		cor_mat = 'N'
	else:
		cor_mat = ReadXY(datadir+cor_mat_ans)
		cor_mat = np.asarray(np.asarray(cor_mat)[1:,1:],dtype='float')
		
	# --------------------------------------------
	# Extract variables needed for initialization
	# --------------------------------------------	
	# Get K for the first generation, but return K_temp to be read into CDClimate module, also get first capture probability back.
	# one check on N0 > 0 and natal
	K = []
	Kstd = []
	pop_capture_back = []
	for isub in xrange(len(K_temp)):
		mu = int(K_temp[isub].split('|')[0])
		sigma = int(Kstd_temp[isub].split('|')[0])
		K.append(mu)
		Kstd.append(sigma)
		pop_capture_back.append(pop_capture_back_pass[isub].split('|')[0])
		if N0[isub] > 0 and natal[isub] == 0:
			print('N0 specified greater than 0 at natal grounds when natal grounds is unsuitable. Initializing N0 at patch ',str(isub+1),' to 0.')
			N0[isub] = 0
	# --------------------------------
	# Initialize subpop field
	# --------------------------------
	subpop = []
	for isub in xrange(len(Pop)):
		for iind in xrange(K[isub]):
			subpop.append(Pop[isub])
	
	# --------------------------------
	# Initialize ID
	# --------------------------------
	id = InitializeID(K,N0)
	
	# ------------------------------------------------
	# Initialize age structure - file and distribution
	# ------------------------------------------------ 	
	tupAgeFile = InitializeAge(K,classvarsfiles,datadir)
	agelst = tupAgeFile[0]
	age_percmort_out = tupAgeFile[1]
	age_percmort_back = tupAgeFile[2]
	age_Mg = tupAgeFile[3]
	age_S = tupAgeFile[4]
	Femalepercent = tupAgeFile[5]
	age_mu = tupAgeFile[6]
	age_size_mean = tupAgeFile[7]
	age_size_std = tupAgeFile[8]
	M_mature = tupAgeFile[9]
	F_mature = tupAgeFile[10]
	age_sigma = tupAgeFile[11]
	age_capture_out = tupAgeFile[12]
	age_capture_back = tupAgeFile[13]
	size_percmort_out = tupAgeFile[14]
	size_percmort_back = tupAgeFile[15]
	age_percmort_out_sd = tupAgeFile[16]
	age_percmort_back_sd = tupAgeFile[17]
	size_percmort_out_sd = tupAgeFile[18]
	size_percmort_back_sd = tupAgeFile[19]
		
	# --------------------------------------------
	# Initialize genetic structure - distribution 
	# --------------------------------------------
	allelst = InitializeGenes(datadir,allefreqfiles,loci,alleles)
	
	# ------------------------------------------------------------------
	# Initialize rest of variables: age,sex,infection,genes,size,mature
	# ------------------------------------------------------------------
	
	age,sex,size,infection,genes,mature,capture,layEggs,recapture,id_N,subpop_N = InitializeVars(K,id,Femalepercent,agelst,cdinfect,loci,alleles,allelst,\
	age_size_mean,age_size_std,subpop,M_mature,F_mature,eggFreq,sizeans,Fmat_set,Mmat_set,Fmat_int,Fmat_slope,Mmat_int,Mmat_slope,cdevolveans,fitvals,burningen)
	
	# ----------------------------------------------
	# Store class variable SubpopIN_Init
	# ----------------------------------------------
	SubpopIN = []
	
	# Get unique patches
	unisubpops = len(Pop)
	
	# Organize type data in SubpopIN - here return this and also update dynamically.
	dtype = [('NatalPop',(str,len(str(unisubpops))+1)),('EmiPop',(str,len(str(unisubpops))+1)),('ImmiPop',(str,len(str(unisubpops))+1)),('EmiCD',float),('ImmiCD',float),('age',int),('sex',int),('size',float),('mature',int),('newmature',int),('infection',int),('name',(str,20)),('capture',int),('recapture',int),('layeggs',float),('genes',(str,3*sum(alleles)+2*loci+2))]
	
	# Get N here - N maybe slighlty different then specified due to random draws
	N = []
	subpopemigration.append([]) # These are tracking variables init here
	subpopimmigration.append([]) # There are tracking variables init here
	for i in xrange(0,unisubpops):
		subpopemigration[0].append([0])
		subpopimmigration[0].append([0])
		SubpopIN.append([])
		N.append([])
		
	# Set class variable by list of populations
	for isub in xrange(unisubpops):
	
		# Get number in this patch
		noinsub = len(np.where(subpop_N == Pop[isub])[0])
		
		# If K is 0
		if noinsub == 0:
			N[isub].append(0) # Track N
			
		# If K does not equal 0
		else:
			N[isub].append(noinsub) # Track N
			# Update the Wright Fisher case for sex here
			# ------------------------------------------
			if Femalepercent[isub][0] == 'WrightFisher':
				# If the subpopulation number is not even then sys exit
				if np.mod(noinsub,2) == 1:
					print("You have WrightFisher turned and this population must be even.")
					sys.exit(-1)
				# Then create half males and females and shuffle
				sex = np.append(np.zeros(noinsub/2,"int"),np.ones(noinsub/2,"int"))
				np.random.shuffle(sex)
			
			# Loop through individuals in subpop
			# ----------------------------------
			for iind in xrange(noinsub):
				# Check if it is an NA spot
				indspot = np.where(subpop_N == Pop[isub])[0][iind]
								
				# Record individual to subpopulation
				# ---------------------------------				
				# Update the Wright Fisher case for sex here
				if Femalepercent[isub][0] == 'WrightFisher':				
					# Subpop,EmiPop(NA),ImmiPop(NA),EmiCD,ImmiCD,age,sex,infection,name/id,capture,recapture,layeggs,genes,mature,newmature
					recd = (subpop_N[indspot],'NA','NA',-9999,-9999,age[indspot],sex[iind],size[indspot],mature[indspot],mature[indspot],infection[indspot],id_N[indspot],capture[indspot],recapture[indspot],layEggs[indspot],repr(genes[indspot]))
					SubpopIN[isub].append(recd)
				
				# Not special Wright Fisher case
				else:			
					# Subpop,EmiPop(NA),ImmiPop(NA),EmiCD,ImmiCD,age,sex,infection,name/id,capture,recapture,layeggs,genes,mature, newmature
					recd = (subpop_N[indspot],'NA','NA',-9999,-9999,age[indspot],sex[indspot],size[indspot],mature[indspot],mature[indspot],infection[indspot],id_N[indspot],capture[indspot],recapture[indspot],layEggs[indspot],repr(genes[indspot]))
					SubpopIN[isub].append(recd)
		# Convert to array with dytpe		
		SubpopIN[isub] = np.asarray(SubpopIN[isub],dtype=dtype)
	# Clean up N
	N = sum(N,[])
		
	# --------------------------
	# Error Checks
	# --------------------------	
	# For now, subpops need to be ordered 1 to N and not skipping, no 0s
	if len(np.where(np.asarray(Pop)=='0')[0]) != 0:
		print('Subpopulation identification field can not have 0 values.')
		sys.exit(-1)
	tempcheck = []
	for i in xrange(len(np.unique(Pop))):
		tempcheck.append(int(np.unique(Pop)[i]))
	tempcheck = np.sort(tempcheck)
	if len(tempcheck) > 1:
		for i in xrange(len(tempcheck)-1):
			if tempcheck[i+1]-tempcheck[i] > 1:
				print('Subpopulation identification field must be labeled sequentially or a single value.')
				sys.exit(-1)	
	
	# Delete other storage variables
	del(size)
	del(age)
	del(id)
	del(genes)
	del(sex)
	del(infection)
	del(subpop)
	del(mature)
	del(capture)
	del(recapture)
	del(layEggs)
	del(subpop_N)
	del(id_N)
	
	# Return this functions variables
	tupPreProcess = ithmcrundir,\
	fitvals,allelst,subpopemigration,subpopimmigration,\
	age_percmort_out,age_percmort_back,age_Mg,age_S,\
	age_mu,age_size_mean,age_size_std,xgridpop,ygridpop,\
	SubpopIN,N,K,dtype,outsizevals,backsizevals,\
	popmort_out,popmort_back,Mg,Str,newmortperc,setmigrate,M_mature,F_mature,age_sigma,outgrowdays,backgrowdays,K_temp,age_capture_out,age_capture_back,Kstd_temp,Kstd,popmort_out_sd,popmort_back_sd,newmortperc_sd,outsizevals_sd,backsizevals_sd,outgrowdays_sd,backgrowdays_sd,size_percmort_out,size_percmort_back,age_percmort_out_sd,age_percmort_back_sd,size_percmort_out_sd,size_percmort_back_sd,pop_capture_back_pass,pop_capture_out,pop_capture_back,natal,cor_mat,migrate
	
	return tupPreProcess	
	#End::DoPreProcess()

# ---------------------------------------------------------------------------------------------------	 		
def DoUserInput(fileans):
	
	'''
	DoUserInput()
	This function reads in the user input and 
	stores the variables.
	'''
	
	# Open file for reading
	inputfile = open(fileans,'r')

	# Read lines from the file
	lines = inputfile.readlines()

	#Close the file
	inputfile.close()

	# Create an empty matrix to append to
	inputvariables = []

	# Split up each line in file and append to empty matrix, x
	for i in lines:
		thisline = i.split(',')
		inputvariables.append(thisline)
		
	# Delete lines
	del(lines)

	return inputvariables
	
	#End::DoUserInput()