import os
import subprocess

DEVICE_LIST = ["nvme1n1"]
CONFIGS = [0, 2, 3]
REPEATS = 5

os.system("/home/kesl/prep.sh")

subprocess.Popen("python3 new_inferencer.py".split(), universal_newlines=True)

for device in DEVICE_LIST:
    for config in CONFIGS:
        for repeat in range(REPEATS):
            
            print(device, config, repeat)
            os.system("modprobe -r nvme && modprobe nvme poll_queues=16")
            os.system("sleep 3")
            os.system(f"echo 0 > /sys/block/{device}/queue/io_poll_delay")
            os.system(f"echo 1 > /sys/block/{device}/queue/pas_enabled")

            os.system(f"fio ./{device}_fio_config/fio_config_{config}.fio > ./fio_result/{device}/rl_12hours/result-config_{config}-repeat_{repeat}.txt")

os.system("killall -9 python3 new_inferencer.py")