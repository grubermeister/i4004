#
#My Intel 4004 Emulator!
#


#Imports
from time import sleep
import sys, binascii, string


#Globals

#Program scratchpad registers, program counters, and program ROM, RAM, and Status
prom, registers, pc_stack, outputs, romIO = [], [], [], [], []
ramBank1, ramBank2, ramBank3, ramBank4 = [], [], [], []
statusChip1, statusChip2, statusChip3, statusChip4 = [], [], [], []

#Subroutine pointer, accumulator, and RAM pointers
activeBank = accumulator = sp = ramp = bankNum = lineNum = 0x0
#Carry and Test flags
carry = test = False

#Number of cycles per instruction
cycles =  [
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #NOP
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, #JCN
  2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, #FIM, SRC
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #FIN, JIN
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, #JUN
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, #JMS
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #INC
  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, #ISZ
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #ADD
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #SUB
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #LD
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #XCH
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #BBL
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #LDM
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, #WRM, WMP, WRR, WR, SBM, RDM, RDR, ADM, RD
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1  #CLB, CLC, IAC, CMC, CMA, RAL, RAR, TCC, DAC, TCS, STC, DAA, KBP, DCL
]


#Functions
def setRpair(rPair, data):
	global registers
	
	#Set Register Pair
	registers[(2*rPair)+1] = data &  0xF
	registers[(2*rPair)]   = data >> 0x4
	
def getRpair(rPair):
	global registers
	
	#Get Register Pair
	return ((registers[2*rPair] << 4) & 0xF0 | registers[2*rPair+1] & 0xF)

def ramAddressDecoder():
	global bankNum, lineNum, test, activeBank
	global ramBank1, ramBank2, ramBank3, ramBank4
	
	if test: activeBank = 1
	bankNum = (ramp & 0x30) >> 4
	lineNum = (ramp & 0xF)
	if activeBank == 1:
		return ramBank1
	elif activeBank == 2:
		return ramBank2
	elif activeBank == 3:
		return ramBank3
	else:
		return ramBank4

def incPC():
	global pc_stack
	
	#Increment Program Counter
	pc_stack[0] += 1
	
def NOP():
	#No Operation
	incPC()
	
def JCN(condition):
	global accumulator, pc_stack, carry, test
	
	#Jump conditionally
	if(condition & 0x4):
		if((not accumulator)^(condition & 0x8)):
			incPC()
			pc_stack[0] = fetchOpCode()
	elif(condition & 0x2):
		if(carry ^ (condition & 0x8)):
			incPC()
			pc_stack[0] = fetchOpCode()
	elif(condition & 0x1):
		if(test ^ (condition & 0x8)):
			incPC()
			pc_stack[0] = fetchOpCode()
	else:
		incPC()
		
def FIM(rPair):
	#Fetch Immediate
	incPC()
	setRpair(rPair, fetchOpCode())
	incPC()
	
def SRC(rPair):
	global ramp
	
	#Send Register Control
	ramp = getRpair(rPair)
	incPC()
	
def FIN(rPair):
	global pc_stack 
	
	#Fetch Indirect
	setRpair(rPair, prom[(pc_stack[0] & 0xF00) | getRpair(0)])
	incPC()

def JIN(rPair):
	global pc_stack, test
	
	#Jump Indirect
	pc_stack[0] = (pc_stack[0] & 0xF00) | getRpair(rPair)
	if test: pc_stack[0] = pc_stack[0] & 0xFF
	
def JUN(address):
	global pc_stack, test
	
	#Jump Unconditional
	incPC()
	pc_stack[0] = address | fetchOpCode()
	if test: pc_stack[0] & 0xFF
	
def JMS(address):
	global pc_stack, sp
	
	#Jump to Subroutine
	incPC()
	address = address | fetchOpCode()
	if sp < 3:
		sp += 1
		for i in range(sp, 0, -1):
			pc_stack[i] = pc_stack[i - 1]
		pc_stack[0] = address
	else:
		print("STACK OVERFLOW")
		incPC()
		
def INC(register):
	global registers
	
	#Increment
	registers[register] += 0x1
	if (registers[register] & 0xF0):
		registers[register] = 0x0
	incPC()
	
def ISZ(register):
	global registers, pc_stack
	
	#Increment and Skip
	incPC()
	registers[register] = (registers[register] + 1) & 0xF
	if (registers[register]):
		pc_stack[0] = (pc_stack[0] & 0xF00) | fetchOpCode()
	else:
		incPC()
		
def ADD(register):
	global registers, carry, accumulator
	
	#Add
	accumulator += registers[register] + (carry)
	carry = False
	if (accumulator & 0xF0):
		accumulator = accumulator & 0xF
		carry = True
	incPC()
	
def SUB(register):
	global registers, carry, accumulator
	
	#Subtract
	accumulator += (~registers[register] & 0xF) + (~carry & 1)
	carry = False
	if (accumulator & 0xF0):
		accumulator = accumulator & 0xF
		carry = True
	incPC()
	
def LD(register):
	global accumulator, registers
	
	#Load
	accumulator = registers(register)
	incPC()
	
def XCH(register):
	global accumulator, registers
	
	#Exchange
	temp = accumulator
	accumulator = registers[register]
	registers[register] = temp
	incPC()
	
def BBL(data):
	global sp, pc_stack, accumulator
	
	#Branch Back and Load
	if sp > 0:
		for i in range(0, sp):
			pc_stack[i] = pc_stack[i+1]
		pc_stack[sp] = 0x0
		sp -= 1
		accumulator = data
	else:
		print("STACK OVERFLOW")
	incPC()
	
def LDM(data):
	global accumulator
	
	#Load Immediate
	accumulator = data
	incPC()
	
def WRM():
	global accumulator, bankNum, lineNum
	global ramp, ramBank1, ramBank2, ramBank3, ramBank4
	
	#Write Main Memory
	ramdata = ramAddressDecoder()
	ramdata[bankNum][lineNum] = accumulator
	incPC()
	
def WMP():
	global activeBank, outputs, accumulator, bankNum, lineNum, test
	
	#Write RAM Port
	outputs[activeBank] = accumulator
	if test: test = (outputs[0] & 0x1)
	incPC()
	
def WRR():
	global romIO, accumulator
	
	#Write ROM Port
	romIO[0] = accumulator
	incPC()
	
def WR(status):
	global activeBank, lineNum, accumulator
	global statusChip1, statusChip2, statusChip3, statusChip4
	
	#Write Status Char
	ramAddressDecoder()
	if activeBank == 1:
		statusChip1[lineNum][status] = accumulator
	elif activeBank == 2:
		statusChip2[lineNum][status] = accumulator
	elif activeBank == 3:
		statusChip3[lineNum][status] = accumulator
	else:
		statusChip4[lineNum][status] = accumulator
	incPC()
	
def SBM():
	global accumulator, carry, bankNum, lineNum
	
	#Subtract Main Memory
	ramdata = ramAddressDecoder()
	accumulator += ((~ramdata[bankNum][lineNum]) & 0xF) + ((~carry) & 1)
	carry = False
	if (accumulator & 0xF0):
		accumulator = accumulator & 0xF
		carry = True
	incPC()
	
def RDM():
	global accumulator, bankNum, lineNum
	
	#Read Main Memory
	ramdata = ramAddressDecoder()
	accumulator = ramdata[bankNum][lineNum]
	incPC()
	
def RDR():
	global test, romIO, outputs, accumulator
	
	#Read ROM Port
	if test: romIO[1] = outputs[1]
	accumulator = romIO[1]
	incPC()
	
def ADM():
	global accumulator, bankNum, lineNum, carry
	
	#Add Main Memory
	ramdata = ramAddressDecoder()
	accumulator += (ramdata[bankNum][lineNum] + carry)
	carry = False
	if (accumulator & 0xF0):
		accumulator & 0xF
		carry = True
	incPC()
	
def RD(status):
	global accumulator, activeBank, bankNum, lineNum
	
	#Read Status Char
	ramAddressDecoder()
	if activeBank == 1:
		accumulator = statusChip1[bankNum][lineNum]
	elif activeBank == 2:
		accumulator = statusChip2[bankNum][lineNum]
	elif activeBank == 3:
		accumulator = statusChip3[bankNum][lineNum]
	else:
		accumulator = statusChip4[bankNum][lineNum]
	incPC()
	
def CLB():
	global accumulator, carry
	
	#Clear Both
	accumulator = 0x0
	carry = False
	incPC()
	
def CLC():
	global carry
	
	#Clear Carry
	carry = False
	incPC()
	
def IAC():
	global accumulator, carry
	
	#Increment Accumulator
	accumulator += 1
	carry = False
	if (accumulator & 0xF0):
		accumulator = accumulator & 0xF
		carry = True
	incPC()
	
def CMC():
	global carry
	
	#Complement Carry
	carry = False if carry == True else False
	incPC()
	
def CMA():
	global accumulator
	
	#Complement
	accumulator = ((~accumulator) & 0xF)
	incPC()
	
def RAL():
	global accumulator, carry
	
	#Rotate Left
	accumulator = (accumulator << 1) | carry
	carry = False
	if (accumulator & 0xF0):
		accumulator = accumulator & 0xF
		carry = True
	incPC()
	
def RAR():
	global accumulator, carry
	
	#Rotate Right
	temp = accumulator & 1
	accumulator = (accumulator >> 1) | (carry << 3)
	carry = temp
	incPC()
	
def TCC():
	global accumulator, carry
	
	#Transfer Carry and Clear
	accumulator = carry
	carry = False
	incPC()
	
def DAC():
	global accumulator, carry
	
	#Decrement Accumulator
	accumulator += 0xF
	carry = False
	if (accumulator & 0xF0):
		accumulator = accumulator & 0xF
		carry = True
	incPC()
	
def TCS():
	global accumulator, carry
	
	#Transfer Carry Subtract
	accumulator = 9 + carry
	carry = False
	incPC()
	
def STC():
	global carry
	
	#Set Carry
	carry = True
	incPC()
	
def DAA():
	global accumulator, carry
	
	#Decimal Adjust Accumulator
	if accumulator > 9:
		accumulator += 6
	carry = False
	if (accumulator & 0xF0):
		accumulator = accumulator & 0xF
		carry = True
	incPC()
	
def DCL():
	global accumulator, activeBank
	
	#Designate Command Line
	switch = accumulator & 0x7
	if switch == 0:
		activeBank = 1
	elif not (switch % 2):
		activeBank = switch * 2
	elif switch == 3:
		activeBank = 3
	elif switch == 5:
		activeBank = 10
	else:
		activeBank = 14
	incPC()

def resetPROM():
	global prom 
	
	#initialize PROM
	if not prom:
		for i in range(0,4096):
			prom.append(0x0)
	else:
		for i in range(0,4096):
			prom[i] = 0x0

def resetRAM():
	global outputs, bankNum, lineNum
	global ramBank1, ramBank2, ramBank3, ramBank4
	global statusChip1, statusChip2, statusChip3, statusChip4
	
	#Reset the shared memory space
	#Starting with the I/O Output Ports
	if not outputs:
		for i in range(0, 8):
			outputs.append(0x0)
	else:
		for i in range(0, 8):
			outputs[i] = 0x0
			
	if not romIO:
		for i in range(0, 4):
			romIO.append(0x0)
	else:
		for i in range(0, 4):
			romIO[i] = 0x0
			
	#RAM Data slots Reset
	if not (ramBank1 and ramBank2 and ramBank3 and ramBank4):
		for i in range(0, 16):
			ramBank1.append([0x0 for j in range(16)])
			ramBank2.append([0x0 for j in range(16)])
			ramBank3.append([0x0 for j in range(16)])
			ramBank4.append([0x0 for j in range(16)])
	else:
		for i in range(0, 16):
			ramBank1[i] = [0x0 for j in range(16)]
			ramBank2[i] = [0x0 for j in range(16)]
			ramBank3[i] = [0x0 for j in range(16)]
			ramBank4[i] = [0x0 for j in range(16)]
			
	#RAM Status Reset
	if not (statusChip1 and statusChip2 and statusChip3 and statusChip4):
		for i in range(0,16):
			statusChip1.append([0x0 for j in range(4)])
			statusChip2.append([0x0 for j in range(4)])
			statusChip3.append([0x0 for j in range(4)])
			statusChip4.append([0x0 for j in range(4)])
	else:
		for i in range(0, 16):
			statusChip1[i] = [0x0 for j in range(4)]
			statusChip2[i] = [0x0 for j in range(4)]
			statusChip3[i] = [0x0 for j in range(4)]
			statusChip4[i] = [0x0 for j in range(4)]
			
	#reset memory location pointer
	bankNum = lineNum = 0x0

def resetCPU():
	global registers,pc_stack,accumulator,carry,test,activeBank
	
	#reset the CPU
	if not registers and (not pc_stack):
		for i in range(0,15):
			registers.append(0x0)
		for i in range(0,3):
			pc_stack.append(0x0)
	else:
		for i in range(0,15):
			registers[i] = 0x0
		for i in range(0,3):
			pc_stack[i] = 0x0
	
	accumulator = 0x0
	activeBank = 1
	carry = test = False

def fetchOpCode():
	global prom, pc_stack
	
	#get opcode value located at the program counter's address in PROM
	return prom[pc_stack[0]]
	
def performOp(instruction):
	global test
	#This is because instructions are 4 bit,
	#so 0xAE is instruction A, register/address E
	operand = instruction % 16
	
	#I'm missing a couple instructions D:
	if instruction == 0x0 or instruction <= 0x09:
		if test: print("NOP")
		NOP()
	elif instruction >= 0x10 and instruction <= 0x1F:
		if test: print("JCN " + str(operand))
		JCN(operand)
	#These calls were tricky to come up with because
	#they don't just take the raw operand...
	elif instruction >= 0x20 and instruction <= 0x2F:
		if not (instruction % 2):
			if test: print("FIM " + str(operand))
			FIM(int(operand / 2)) #So 0xE (14) will call FIM(7)
		else:
			if test: print("SRC " + str(operand))
			SRC(int((operand - 1) / 2)) #So 0xD (13 - 1) will call SRC(6)
	elif instruction >= 0x30 and instruction <= 0x3F:
		if not (instruction % 2):
			if test: print("FIN " + str(operand))
			FIN(int(operand / 2))
		else:
			if test: print("JIN " + str(operand))
			JIN(int((operand - 1) / 2))
	elif instruction >= 0x40 and instruction <= 0x4F:
		if test: print("JUN " + str(operand))
		JUN(int(operand & 0xF00))
	elif instruction >= 0x50 and instruction <= 0x5F:
		if test: print("JMS " + str(operand))
		JMS(int(operand & 0xF00))
	elif instruction >= 0x60 and instruction <= 0x6F:
		if test: print("INC " + str(operand))
		INC(operand)
	elif instruction >= 0x70 and instruction <= 0x7F:
		if test: print("ISZ " + str(operand))
		ISZ(operand)
	elif instruction >= 0x80 and instruction <= 0x8F:
		if test: print("ADD " + str(operand))
		ADD(operand)
	elif instruction >= 0x90 and instruction <= 0x9F:
		if test: print("SUB " + str(operand))
		SUB(operand)
	elif instruction >= 0xA0 and instruction <= 0xAF:
		if test: print("LD " + str(operand))
		LD(operand)
	elif instruction >= 0xB0 and instruction <= 0xBF:
		if test: print("XCH " + str(operand))
		XCH(operand)
	elif instruction >= 0xC0 and instruction <= 0xCF:
		if test: print("BBL " + str(operand))
		BBL(operand)
	elif instruction >= 0xD0 and instruction <= 0xDF:
		if test: print("LDM " + str(operand))
		LDM(operand)
	elif instruction == 0xE0:
		if test: print("WRM")
		WRM()
	elif instruction == 0xE1:
		if test: print("WMP")
		WMP()
	elif instruction == 0xE2:
		if test: print("WRR")
		WRR()
	elif instruction == 0xE4:
		if test: print("WR 0")
		WR(0)
	elif instruction == 0xE5:
		if test: print("WR 1")
		WR(1)
	elif instruction == 0xE6:
		if test: print("WR 2")
		WR(2)
	elif instruction == 0xE7:
		if test: print("WR 3")
		WR(3)
	elif instruction == 0xE8:
		if test: print("SBM")
		SBM()
	elif instruction == 0xE9:
		if test: print("RDM")
		RDM()
	elif instruction == 0xEA:
		if test: print("RDR")
		RDR()
	elif instruction == 0xEB:
		if test: print("ADM")
		ADM()
	elif instruction == 0xEC:
		if test: print("RD 0")
		RD(0)
	elif instruction == 0xED:
		if test: print("RD 1")
		RD(1)
	elif instruction == 0xEE:
		if test: print("RD 2")
		RD(2)
	elif instruction == 0xEF:
		if test: print("RD 3")
		RD(3)
	elif instruction == 0xF0:
		if test: print("CLB")
		CLB()
	elif instruction == 0xF1:
		if test: print("CLC")
		CLC()
	elif instruction == 0xF2:
		if test: print("IAC")
		IAC()
	elif instruction == 0xF3:
		if test: print("CMC")
		CMC()
	elif instruction == 0xF4:
		if test: print("CMA")
		CMA()
	elif instruction == 0xF5:
		if test: print("RAL")
		RAL()
	elif instruction == 0xF6:
		if test: print("RAR")
		RAR()
	elif instruction == 0xF7:
		if test: print("TCC")
		TCC()
	elif instruction == 0xF8:
		if test: print("DAC")
		DAC()
	elif instruction == 0xF9:
		if test: print("TCS")
		TCS()
	elif instruction == 0xFA:
		if test: print("STC")
		STC()
	elif instruction == 0xFB:
		if test: print("DAA")
		DAA()
	elif instruction == 0xFD:
		if test: print("DCL")
		DCL()
	else:
		#How did this get in here?
		if test: print("XXX")
		NOP()

def runCPU(cycleLimit):
	global prom 
	#we're only allowed to execute so many instructions per emulated clock cycle,
	#accurate timing, and all that.
	cycleCounter = 0
	
	while cycleCounter < cycleLimit:
		code = fetchOpCode()
		performOp(code)
		cycleCounter += cycles[code]

def dumpCore():
	print("REGISTERS:")
	for r in registers:
		sys.stdout.write(str(r) + ", ")
	print("\nSTACK:")
	for p in pc_stack:
		sys.stdout.write(str(p) + ", ")
	print("\nACCUMULATOR:")
	print(accumulator)
	print("CARRY:")
	print(carry)
	print("OUTPUTS:\n" + str(outputs) + "\n" + str(romIO))

def main():
	global prom, test
	#we need to know where in our PROM the program monitor will be writing
	temp = 0
	
	resetPROM()
	resetRAM()
	resetCPU()
	#program monitor
	while True:
		line = input('? ')
		line = line.upper().replace(' ', '')
		if line == 'Q' or line == 'QUIT' or line == 'EXIT' or line == 'END' or line == 'STOP':
			#quit
			break
		elif line == '!' or line == 'RUN' or line == 'EXECUTE' or line == 'START':
			#execute PROM;
			#This cycle limit is completely arbitrary...
			#I tried to make it hardware accurate, but it just didn't seem right
			runCPU(2600)
			print(str(outputs))
			print(str(romIO))
		elif line == 'SHOW':
			#Dump out some info for us, will ya?
			line = input('SHOW: ')
			line = line.upper()
			if line == 'RAM':
				if activeBank == 1:
					for val in ramBank1:
						print(str(val))
				if activeBank == 2:
					for val in ramBank2:
						print(str(val))
				if activeBank == 3:
					for val in ramBank3:
						print(str(val))
				if activeBank == 4:
					for val in ramBank4:
						print(str(val))
			if line == 'BANK':
				print(str(activeBank))
			if line == 'ROM':
				for i in range(0, temp):
					print(format(prom[i], '02X'))
		elif line == 'F' or line == 'FLUSH' or line == 'CLEAR' or line == 'PURGE' or line == 'RESET':
			#flush PROM, RAM, and reset the CPU
			temp = 0
			resetPROM()
			resetRAM()
			resetCPU()
		elif line == '?' or line == 'STEP' or line == 'DEBUG':
			#processor is in debug mode
			test = True
			runCPU(1)
			dumpCore()
		elif line == 'SAVE':
			line = input('FILE: ')
			line = line.upper()
			with open(line, 'wb') as rom:
				out = bytearray(prom[0:temp])
				rom.write(bytes(out))
				rom.close()
			print("OK")
		elif line == 'LOAD':
			line = input('FILE: ')
			line = line.upper()
			with open(line, 'rb') as rom:
				load = rom.read()
				for i in bytearray(load):
					prom[temp] = i
					temp += 1
		else:
			if temp >= 4095:
				#PROM is limited to 4K
				print("PROM FULL\n")
			else:
				if all(c in string.hexdigits for c in line):
					#passes the sniff test, slot it into PROM!
					for i in range(0, len(line), 2):
						prom[temp] = int(line[i:i+2], 16)
						temp += 1
				else:
					#tried to feed me some bullshit, hoss
					print("SYNTAX INVALID")

if __name__ == '__main__':
	main()
