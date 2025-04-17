fake = "sA s2 s3 s4 s5 s6 s7 s8 s9 sX sJ sQ sK hA h2 h3 h4 h5 h6 h7 h8 h9 hX hJ hQ hK cA c2 c3 c4 c5 c6 c7 c8 c9 cX cJ cQ cK dA d2 d3 d4 d5 d6 d7 d8 d9 dX dJ dQ dK".strip()
from tqdm import tqdm
from pwn import remote, process
# run with env SEED=1234
# r = process("./holographic", env={"SEED": "1234"})

r = remote("holographic-23seeordn6w4k.shellweplayaga.me", 1337)
ticket = 'ticket{GarfieldZombie8126n25:tuy9LZF60O9Bv7TvJfcGAW-_bab54BV3HCrxnTGCeYDgHeuj}'
r.sendline(ticket)


seeds = {}

for _ in tqdm(range(35000)):
    r.sendline(fake)

for _ in tqdm(range(35000)):
    r.recvuntil(b'seed: ')
    seed = r.recvline().strip()
    r.recvuntil(b'Oh no, were you bluffing too?\n')
    resp = r.recvline()
    seeds[seed] = resp

for _ in tqdm(range(35000)):
    r.sendline(fake)

for _ in tqdm(range(35000)):
    r.recvuntil(b'seed: ')
    seed = r.recvline().strip()
    r.recvuntil(b'Oh no, were you bluffing too?\n')
    resp = r.recvline()
    seeds[seed] = resp


for i in tqdm(range(65537)):
    r.recvuntil(b'seed: ')
    seed = r.recvline().strip()
    if seed in seeds:
        print('diocanissimo')
        r.sendline(seeds[seed])
        r.interactive()
        break

    r.sendline(fake)
    r.recvuntil(b'Oh no, were you bluffing too?\n')
    resp = r.recvline()
    if seed not in seeds:
        seeds[seed] = resp

r.interactive()