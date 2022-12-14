import os

DEVICE_LIST = ["nvme1n1"]
CONFIGS = [0, 2, 3]
REPEATS = 5

os.system("/home/kesl/prep.sh")

for device in DEVICE_LIST:
    for config in CONFIGS:
        for repeat in range(REPEATS):
            
            print(device, config, repeat, "INT")
            os.system("modprobe -r nvme && modprobe nvme")
            os.system("sleep 3")
            os.system(f"fio ./{device}_fio_config/int_fio_config_{config}.fio > ./fio_result/{device}/int/result-config_{config}-repeat_{repeat}.txt")
            os.system("sleep 1")

            print(device, config, repeat, "PAS")
            os.system("modprobe -r nvme && modprobe nvme poll_queues=16")
            os.system("sleep 3")
            os.system(f"echo 0 > /sys/block/{device}/queue/io_poll_delay")
            os.system(f"echo 1 > /sys/block/{device}/queue/pas_enabled")
            os.system(f"fio ./{device}_fio_config/fio_config_{config}.fio > ./fio_result/{device}/pas/result-config_{config}-repeat_{repeat}.txt")
            os.system("sleep 1")
            

            print(device, config, repeat, "CP")
            os.system("modprobe -r nvme && modprobe nvme poll_queues=16")
            os.system("sleep 3")
            os.system(f"fio ./{device}_fio_config/fio_config_{config}.fio > ./fio_result/{device}/cp/result-config_{config}-repeat_{repeat}.txt")
            os.system("sleep 1")
            