#!/usr/bin/env python
import queue
import pandas as pd
import math
from pathlib import Path
import sys
import copy

sys.setrecursionlimit(10000)
G = [{}]
time_table = {}
arrive_table = {}
number_of_connections = {} # 接続路線数
goal_stations = ["横浜", "品川", "立川", "熱海"]
start = "新宿"
routes = []
one_of_routes = []
used = []
branch_stations = []

# 時刻表ファイル読み込み関数
def import_time_table():
	path = Path("./csv/")
	path_list = path.glob("*.csv")
	loaded_list = []
	for csv in path_list:
		flag = 0 # 接続路線判定用
		route_name = str(csv)[:-6] # 路線名
		if route_name not in loaded_list:
			loaded_list.append(route_name)
			flag = 1
		df = pd.read_csv(csv, header=None, index_col=0, 
										skiprows=9, skipfooter=1, engine="python", encoding="utf-8")
		#print(df)
		for row in range(len(df)):
			for column in range(1, len(df.columns)):
				if not math.isnan(df.iloc[row, column]):
					if int(df.iloc[row, column]) < 200:
						df.iloc[row, column] = int(df.iloc[row, column]) + 2400

		loaded_stations_list = [] # 同一路線で同一駅が登場した際（環状線）に重複カウントを避けるためのリスト
		for station_num in range(len(df)):
			# 接続路線数を増加
			if (flag == 1) and (df.index[station_num] not in loaded_stations_list):
				loaded_stations_list.append(df.index[station_num])
				# if df.index[station_num] in number_of_connections.keys():
				# 	number_of_connections[df.index[station_num]] = number_of_connections[df.index[station_num]] + 1
				# else:
				# 	number_of_connections[df.index[station_num]] = 1
			if df.iloc[station_num, 0] == "発":
				if station_num < (len(df) - 1):
					time_list = []
					for time in range(1, len(df.columns)):
						if not (math.isnan(df.iloc[station_num, time]) or  math.isnan(df.iloc[station_num+1, time])):
							div = (df.iloc[station_num+1, time] // 100) - (df.iloc[station_num, time] // 100)
							if div >= 1:
								time_list.append([int(df.iloc[station_num, time]), int((df.iloc[station_num+1, time] - 40*div)-df.iloc[station_num, time])])
							else:
								time_list.append([int(df.iloc[station_num, time]), int(df.iloc[station_num+1, time]-df.iloc[station_num, time])])
					time_list.reverse()
					elements = [df.index[station_num+1], time_list]
					if df.index[station_num] in time_table.keys():
						#print(df.index[station_num])
						new_value = time_table[df.index[station_num]]
						for value in new_value:
							if value[0] == elements[0]:
								elements = [value[0], value[1]+elements[1]]
								time_table[df.index[station_num]].remove(value)
								break
						else:
							number_of_connections[df.index[station_num]] = number_of_connections[df.index[station_num]] + 1
						new_value.append(elements)
						time_table[df.index[station_num]] = new_value
					else:
						number_of_connections[df.index[station_num]] = 1
						new_value = []
						new_value.append(elements)
						time_table[df.index[station_num]] = new_value
			elif df.iloc[station_num, 0] == "着":
				if station_num > 0:
					arrive_time = []
					for time in range(1, len(df.columns)):
						if not math.isnan(df.iloc[station_num, time]):
							arrive_time.append(int(df.iloc[station_num, time]))
					elements = [df.index[station_num-1], arrive_time]
					if df.index[station_num] in arrive_table.keys():
						new_value = arrive_table[df.index[station_num]]
						new_value.append(elements)
						arrive_table[df.index[station_num]] = new_value
					else:
						new_value = []
						new_value.append(elements)
						arrive_table[df.index[station_num]] = new_value
	for table in time_table.values():
		for st in table:
			st[1].sort(key=lambda x: x[0], reverse=True)

# ルート取得関数
# スタートからゴールまでの1ルートをゴールから逆算して取得する
def calculate_last_train(goal):
	global one_of_routes # ルート格納リスト
	global used # 登場済駅リスト
	prev_station = goal # 仕組み上は逆にたどるので前の駅だが、実際はゴールに近い駅
	# ルート取得ループ
	while prev_station != start:
		departure_list = search_stations(prev_station) # prev_stationの隣の駅のリストを取得
		#print(departure_list)
		# ほんとは1周でいいはず、、、
		for departure in departure_list:
		#departure = departure_list[0]
			stations = [departure, prev_station]
			#print(stations)
			if stations not in used:
				# 分岐駅ではどの分岐に入ったかをusedに記録
				if number_of_connections[prev_station] > 1:
					if prev_station not in branch_stations:
						branch_stations.append(prev_station)
					used.append(stations)
				used.append([prev_station, departure])
				# 既存のルートに接続したら終了
				for route in routes:
					for node in route:
						if node[1] == departure:
							one_of_routes.append([departure, prev_station])
							return True
				# ゴールにたどり着けばTrueが返ってくる
				if calculate_last_train(departure):
					one_of_routes.append([departure, prev_station])
					return True
		# どの隣の駅を選んでもゴールに着かなければルート誤り
		else:
			return False
	else:
		return True

# 分岐する駅を基準に別ルートを取得する
# branch_stations: 分岐駅のリスト
def another_route(goal, branch_stations):
	global one_of_routes # 既に取得した1ルート

	for branch_station in branch_stations:
		#print(branch_station)
		# elements_of_another_route = [] # 分岐駅までのルートを格納するリスト
		# 分岐駅からゴールまでの区間を取得
		for i in range(len(search_stations(branch_station))-1):
			if calculate_last_train(branch_station):
				#print(one_of_routes)
				add_route = copy.copy(one_of_routes)
				if add_route[-1][1] != goal:
					#print(add_route, goal)
					elements_of_another_route = before_joining(add_route, branch_station)
					for element in elements_of_another_route:
						if element[0][0] != start:
							add_route = after_joining(element, element[0][0])
						else:
							add_route = element
						#print(add_route)
						routes.append(add_route)
						#print(add_route)
				else:
					elements_of_another_route = add_route
					if elements_of_another_route[0][0] != start:
						add_route = after_joining(elements_of_another_route, elements_of_another_route[0][0])
					routes.append(add_route)
					#print(add_route)
				one_of_routes = []

def before_joining(route_list, branch_station):
	elements_of_another_route = []
	for route in routes:
		#route.reverse()
		# 分岐駅までのルートをelements_of_another_routeに追加
		# node:[出発駅, 到着駅]
		for i, node in enumerate(reversed(route)):
			# スタートから分岐駅に到着する区間までを取得
			if node[1] == branch_station:
				elements_of_another_route.append(route_list + route[-i:])
	#print(elements_of_another_route)
	return elements_of_another_route

# 分岐したルートが再合流してからのルートを取得
# [a, b]のaがstationと一致したところからゴールまでをルートに追加する
def after_joining(route_list, station):
	additional_routes = []
	copy_route_list = copy.copy(route_list)
	#additional_routes.reverse()
	for route in routes:
		rev_route = route[::-1]
		for i, node in enumerate(route):
			if node[0] == station:
				additional_routes = route[:i]
				break
	additional_routes.extend(copy_route_list)
	#additional_routes.reverse()
	return additional_routes

def double_check(branch_stations):
	copy_branch_stations = copy.copy(branch_stations)
	for branch_station in copy_branch_stations:
		departure_list = search_stations(branch_station)
		for departure in departure_list:
			if not ([departure, branch_station] in one_of_routes or [branch_station, departure] in one_of_routes):
				break
		else:
			branch_stations.remove(branch_station)
	return branch_stations


def search_stations(arrival):
	departure_list = []
	for departure in arrive_table[arrival]:
		departure_list.append(departure[0])
	return departure_list

def calculate_route(departure, arrival, arrival_time):
	#print(departure, arrival, arrival_time)
	for dep_station in time_table[departure]:
		if dep_station[0] == arrival:
			#print(time_table[departure])
			#print(dep_station[1])
			for departure_time in dep_station[1]:
				if departure_time[0] is not None:
					if departure_time[0] + departure_time[1] <= arrival_time:
						return departure_time[0]
	return None

# 時間変換関数
# HHmmのmmが60以上のときに繰り上げて正しい表記にする
def convert_time(original_time):
	if original_time % 100 >= 60:
		time = original_time + 40
	else:
		time = original_time
	return time

# よくわかんないやついらない？→いらない。
# ここに来たroutesはもうスタートからゴールまできれいに並んでいる
# def print_routes(routes):
# 	for leaf in range(1, len(routes)):
# 		for root in range(leaf-1, -1, -1):
# 			for i, node in enumerate(routes[root]):
# 				if routes[leaf][-1][1] == node[0]:
# 					add = routes[root][i:]
# 					one_of_routes = routes[leaf]
# 					for ad in add:
# 						one_of_routes.append(ad)
# 					routes[leaf] = one_of_routes
# 	calculate_time(routes)

def calculate_time(routes):
	for route in routes:
		time_list = []
		for arrival in arrive_table[route[::-1][0][1]]:
			if route[::-1][0][0] == arrival[0]:
				departure_time = arrival[1][-1]
		time_list.append([route[::-1][0][1], departure_time])
		for node in route[::-1]:
			departure_time = calculate_route(node[0], node[1], departure_time)
			time_list.append([node[0], departure_time])
			if departure_time is None:
				# for i in time_list:
				# 	print(i)
				# print("\n")
				time_list.clear()
				break
		if len(time_list) > 0:
			for i in time_list:
				print(i)
			print("\n")

# ルート内の重複区間を削除
def delete_duplication(routes):
	for num, route in enumerate(routes):
		#del_list = []
		while(not is_unique(route)):
			copy_route = copy.copy(route)
			del_node_list = []
			for i, node in enumerate(copy_route):
				start = node[0]
				num_start = i
				if num_start + 1 <= len(copy_route):
					for end_node in range(num_start+1, len(copy_route)):
						if start == copy_route[end_node][1]:
							del_node_list.extend(copy_route[num_start:end_node+1])
							#del_list.append([num_start, end_node+1])
			del_node_list_unique = get_unique_list(del_node_list)
			#print(del_node_list_unique)
			#print(route)
			for del_node in del_node_list_unique:
				#print(del_node)
				route.remove(del_node)
			#print(route)
		#copy_routes[num] = copy_route
	#print(routes)
	copy_routes = copy.copy(routes)
	for num in range(len(copy_routes)-1):
		for m in range(num+1, len(copy_routes)):
			if copy_routes[num] == copy_routes[m]:
				routes.remove(copy_routes[m])
				break

def get_unique_list(seq):
	seen = []
	return [x for x in seq if x not in seen and not seen.append(x)]

def is_unique(seq):
	seen = []
	unique_list = [x for x in seq if x not in seen and not seen.append(x)]
	return len(seq) == len(unique_list)

import_time_table()
#print(time_table)
#print(arrive_table)
for goal in goal_stations:
	last_arrive = 2600
	calculate_last_train(goal)
	routes.append(one_of_routes)
	#print(one_of_routes)
	#print(used)
	#print_routes(routes)
	#branch_stations = double_check(branch_stations)
	#print(branch_stations)
	#print(number_of_connections)
	one_of_routes = []
	another_route(goal, branch_stations)
	#for route in routes:
	#	print(route)
	#delete_duplication(routes)
	calculate_time(routes)
	#for route in routes:
	#	print(route)
	routes = []
	used = []
	branch_stations.clear()

