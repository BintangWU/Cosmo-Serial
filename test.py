import rk_mcprotocol as mc
import time


PLC_HOST = "172.16.100.100"
PLC_PORT = 1025
plc = mc.open_socket(PLC_HOST, PLC_PORT)


if __name__ == "__main__":
    try:
        start_time = time.time()
        print(mc.read_sign_word(plc,headdevice = 'd0' , length = 2, signed_type=False))
        mc.write_sign_word(plc, headdevice= 'd1', data_list= [123, -456], signed_type=True)
        mc.write_bit(plc, headdevice= 'm0', data_list= [1, 0, 1])
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.4f} seconds")
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")