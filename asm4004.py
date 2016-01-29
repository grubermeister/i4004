#
# My Intel 4004 Assembler!
#

#Imports
import sys


#Functions
def clean_up(*handles):
	
	#Close out our file handles nicely, and exit
	try:
		for handle in handles:  handle.close()
		exit()
	except Exception as e:
		return e
		
def JCN(operand):
	operand = operand.split(',')
	condition = {'00':'10', 'TZ':'11', 'CN':'12', 'TC':'13', 'AZ':'14',
	             'TA':'15', 'CA':'16', 'NN':'17', 'NZ':'18', 'TN':'19',
	             'CZ':'1A', 'N3':'1B', 'AN':'1C', 'N5':'1D', 'NC':'1E',
	             'FF':'1F'}
	             
	if len(operand) == 2:
		try:
			output = condition[operand[0]]
			if operand[1][0] == '$':  output += operand[1][1:3]
			else:  raise
		except:
			return None
	else:
		return None
		
	return output
	
	
def FIM(operand):
	operand = operand.split(',')
	
	if len(operand) == 2:
		pair = int(operand[0][1:2]) * 2
		if operand[0][0] == 'P' and pair < 8:  output = '2' + str(pair)
		else:  return None
		if operand[1][0].isdigit() and len(operand[1]) == 2:  output += format(int(operand[1][1:3]), '02X')
		else:  return None
	else:
		return None
		
	return output
	
def SRC(operand):
	pair = int(operand[1:2]) * 2
	
	if len(operand) == 2 and operand[0] == 'P' and pair < 8:  
		pair += 1; output = '2' + str(pair)
	else:  
		return None
	
	return output
	
def FIN(operand):
	pair = int(operand[1:2]) * 2
	
	if len(operand) == 2 and operand[0] == 'P' and pair < 8:  output = '3' + str(pair)
	else:  return None
		
	return output
	
def JIN(operand):
	pair = int(operand[1:2]) * 2
	
	if len(operand) == 2 and operand[0] == 'P' and pair < 8:
		pair += 1; output = '3' + str(pair)
	else:
		return None
		
	return output
	
def JUN(operand):
	if operand[0] == '$' and len(operand) < 5:
		output = '4' + operand[1]
		output += operand[2:4]
	else:
		return None
		
	return output
	
def JMS(operand):
	if operand[0] == '$' and len(operand) < 5:
		output = '5' + operand[1]
		output += operand[2:4]
	else:
		return None
		
	return output
	
def INC(operand):
	if operand[0] == 'R' and len(operand) == 2:  output = '6' + operand[1]
	else:  return None
	
	return output
	
def ISZ(operand):
	operand = operand.split(',')
	
	if len(operand) == 2:
		if operand[0][0] == 'R' and len(operand[0]) == 2:  output = '7' + operand[0][1]
		else:  return None
		if operand[1][0] == '$' and len(operand[1]) == 3:  output += operand[1][1:3]
		else:  return None
	else:
		return None
		
	return output
	
def ADD(operand):
	if operand[0] == 'R' and len(operand) < 2:  output = '8' + operand[1]
	else:  return None
	
	return output
	
def SUB(operand):
	if operand[0] == 'R' and len(operand) < 2:  output = '9' + operand[1]
	else:  return None
	
	return output
	
def LD(operand):
	if operand[0] == 'R' and len(operand) < 2:  output = 'A' + operand[1]
	else:  return None
	
	return output
	
def XCH(operand):
	if operand[0] == 'R' and len(operand) == 2:  output = 'B' + operand[1]
	else:  return None
	
	return output
	
def BBL(operand):
	if operand[0].isdigit() and len(operand) < 3: output = 'C' + format(int(operand), 'X')
	else:  return None
	
	return output
	
def LDM(operand):
	if operand[0].isdigit() and len(operand) < 3: output = 'D' + format(int(operand), 'X')
	else:  return None
	
	return output
	
def assembler(mnemonic, operand):
	if operand:  operand = operand.replace(' ', '').upper()

	opList = {'NOP':'00', 'WRM':'E0', 'WMP':'E1', 'WRR':'E2', 'WR0':'E4',
	          'WR1':'E5', 'WR2':'E6', 'WR3':'E7', 'RD1':'ED', 'RD2':'EE',
	          'SBM':'E8', 'RDM':'E9', 'RDR':'EA', 'ADM':'EB', 'RD0':'EC',
	          'CLB':'F0', 'CLC':'F1', 'IAC':'F2', 'CMC':'F3', 'CMA':'F4',
	          'RAL':'F5', 'RAR':'F6', 'TCC':'F7', 'DAC':'F8', 'TCS':'F9',
	          'STC':'FA', 'DAA':'FB', 'DCL':'FD', 'RD3':'EF'}
	
	#Performs the actual assembling of the ROM
	if mnemonic in opList: return opList[mnemonic]
	elif mnemonic == 'JCN' and (operand):  return JCN(operand)
	elif mnemonic == 'FIM' and (operand):  return FIM(operand)
	elif mnemonic == 'SRC' and (operand):  return SRC(operand)
	elif mnemonic == 'FIN' and (operand):  return FIN(operand)
	elif mnemonic == 'JIN' and (operand):  return JIN(operand)
	elif mnemonic == 'JUN' and (operand):  return JUN(operand)
	elif mnemonic == 'JMS' and (operand):  return JMS(operand)
	elif mnemonic == 'INC' and (operand):  return INC(operand)
	elif mnemonic == 'ISZ' and (operand):  return ISZ(operand)
	elif mnemonic == 'ADD' and (operand):  return ADD(operand)
	elif mnemonic == 'SUB' and (operand):  return SUB(operand)
	elif mnemonic == 'LD'  and (operand):  return LD(operand)
	elif mnemonic == 'XCH' and (operand):  return XCH(operand)
	elif mnemonic == 'BBL' and (operand):  return BBL(operand)
	elif mnemonic == 'LDM' and (operand):  return LDM(operand)
	else:  return None
	
def main():
	params   = sys.argv; outlist = ''
	
	print "ASM 4004 - build 01/26/16\n"
	if len(params) != 2:
		print "Usage:  asm4004 [filename.asm]"
		exit()
	#Name of the ROM we're assembling
	progName = params[1].split('.')[0].upper() + ".ROM"
	inFile  = open(params[1], 'r')
	for inLine in enumerate(inFile.read().splitlines(), start=1):
		if not inLine[1][0] == ';':
			instruction = inLine[1].split(' ', 1)
			if len(instruction) == 1:  instruction.append(None)
			outlist += assembler(instruction[0], instruction[1])
	outlist = outlist.decode("hex")
	outFile = open(progName, 'w')
	outFile.write(outlist)
	
	print "OK"
	print clean_up(inFile)

if __name__ == '__main__':
	main()
