import docker
import json
import time

# format = '%Y-%m-%dT%H:%M:%S.%f'
# date_string = '2019-11-17T22:45:55.089107429Z'
# datetime.datetime.strptime(date_string[:-4], format)

prevCPU = 0.0
prevSystem = 0.0
prev_tx_bytes = 0.0
prev_time = 0.0

def calcCPUPercent(previousCPU, previousSystem, v):
    cpuPercent = 0.0
    # calculate the change for the cpu usage of the container in between readings
    cpuDelta = v['cpu_stats']['cpu_usage']['total_usage'] - previousCPU
    # calculate the change for the entire system between readings
    systemDelta = v['cpu_stats']['system_cpu_usage'] - previousSystem
    if systemDelta > 0.0 and cpuDelta > 0.0:
        cpuPercent = (cpuDelta / systemDelta) * len(v['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0

    return cpuPercent

def calcNet(previous_tx_bytes, curr_tx_bytes, delta_t, bw):
	tx_rate = (curr_tx_bytes - previous_tx_bytes)/delta_t
	return tx_rate/bw

cli = docker.APIClient(base_url='tcp://172.17.74.183:2375')
stats_obj = cli.stats('rmq')
for stat in stats_obj:
	curr_time = time.time()
	data = json.loads("".join( chr(x) for x in stat))
	cpu = calcCPUPercent(prevCPU, prevSystem, data)
	mem = (data['memory_stats']['usage']/data['memory_stats']['limit']) * 100.0
	# calculate net 
	tx_bytes = 0.0
	for intf in data['networks']:
		tx_bytes += data['networks'][intf]['tx_bytes']
	delt = curr_time - prev_time
	net = calcNet(prev_tx_bytes, tx_bytes, delt, 1000000.0)
	# store current stats
	prevCPU = data['cpu_stats']['cpu_usage']['total_usage']
	prevSystem = data['cpu_stats']['system_cpu_usage']
	prev_tx_bytes = tx_bytes
	prev_time = time.time()
	# calculate vol
	rvol = (1-cpu/100) * (1 - mem) * (1 - net)
	vol = 1/rvol
	print('CPU USAGE: ' + str(cpu) + ' MEM: ' + str(mem) + ' NET: ' + str(net) + ' VOL: ' + str(vol))
