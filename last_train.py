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
goal_stations = ["横浜"]
start = "新宿"
routes = []
one_of_routes = []
used = []
branch_stations = []

# 時刻表ファイル読み込み関数
def import_time_table():
	path = Path("./csv/")
	path_list = path.glob("*.csv")
	for csv in path_list:
		df = pd.read_csv(csv, header=None, index_col=0, 
										skiprows=9, skipfooter=1, engine="python", encoding="utf-8")
		#print(df)
		for row in range(len(df)):
			for column in range(1, len(df.columns)):
				if not math.isnan(df.iloc[row, column]):
					if int(df.iloc[row, column]) < 200:
						df.iloc[row, column] = int(df.iloc[row, column]) + 2400

		for station_num in range(len(df)):
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
						new_value = time_table[df.index[station_num]]
						new_value.append(elements)
						time_table[df.index[station_num]] = new_value
					else:
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

# ルート取得関数
# スタートからゴールまでの1ルートをゴールから逆算して取得する
def calculate_last_train(goal):
	global one_of_routes # ルート格納リスト
	global used # 登場済駅リスト
	prev_station = goal
	# ルート取得ループ
	while prev_station != start:
		departure_list = search_stations(prev_station) # prev_stationの隣の駅のリストを取得
		print(departure_list)
		# ルート枝分かれの確認
		if len(departure_list) > 1:
			branch_stations.append(prev_station) # branch_stations:ルートが枝分かれする駅のリスト
		# ほんとは1周でいいはず、、、
		for departure in departure_list:
		#departure = departure_list[0]
			stations = [departure, prev_station]
			#print(stations)
			if stations not in used:
				used.append(stations) # 枝分かれする時だけ追加すればいいんじゃない？
				#used.append(stations[::-1])
				#route.append([departure, prev_station])
				#print(departure + ":::")
				ans = calculate_last_train(departure)
				one_of_routes.append([departure, prev_station])
				#print(route)
				#prev_station = used[-1][0]
				#print(prev_station + "::::" + used[-1][0])
			#else:
				#route = []
				#print(stations)
				#print(":::::::::")
				return prev_station
		else:
			return prev_station
	else:
		#route.reverse()
		#print(route)
		#routes.append(route)
		#route = []
		return prev_station

# 分岐する駅を基準に別ルートを取得する
# branch_stations: 分岐駅のリスト
def another_route(branch_stations):
	global one_of_routes # 既に取得した1ルート

	for branch_station in branch_stations:
		elements_of_another_route = [] # 分岐駅までのルートを格納するリスト
		#print(routes)
		# 全てのルートで分岐駅までのルート取得
		for route in routes:
			#route.reverse()
			# 分岐駅までのルートをelements_of_another_routeに追加
			# node:[出発駅, 到着駅]
			for i, node in enumerate(reversed(route)):
				# スタートから分岐駅に到着する区間までを取得
				if node[1] == branch_station:
					elements_of_another_route.append(route[-i:][::-1])
		calculate_last_train(branch_station)
		print(one_of_routes)
		for i, beginning_node in enumerate(one_of_routes):
			if beginning_node[0] == branch_station:
				beginning_of_section = i
				for end_node in range(beginning_of_section+1, len(one_of_routes)):
					for route in routes:
						for node_in_route in route:
							if (one_of_routes[end_node][0] == node_in_route[0]) and (one_of_routes[end_node][0] != branch_station):
								print(one_of_routes[end_node][0], node_in_route[0])
								end_of_section = end_node
								print(beginning_of_section, end_of_section)
								break
							elif one_of_routes[end_node][1] == branch_station:
								break
						else:
							continue
						break
					else:
						continue
					break
				else:
					continue
		one_of_routes = one_of_routes[beginning_of_section:end_of_section]
		print(one_of_routes)
		after_joining(one_of_routes[-1][1])
		#print(routes)
		break

# 分岐したルートが再合流してからのルートを取得
# [a, b]のaがstationと一致したところからゴールまでをルートに追加する
def after_joining(station):
	additional_routes = copy.copy(one_of_routes)
	#additional_routes.reverse()
	print(routes)
	for route in routes:
		rev_route = route[::-1]
		for i, node in enumerate(route):
			if node[0] == station:
				additional_routes.extend(route[:i])
				break
	#additional_routes.reverse()
	print(additional_routes)

def double_check(branch_stations):
	copy_branch_stations = copy.copy(branch_stations)
	print(copy_branch_stations)
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
	for dep_station in time_table[departure]:
		if dep_station[0] == arrival:
			for departure_time in dep_station[1]:
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

def print_routes(routes):
	for leaf in range(1, len(routes)):
		for root in range(leaf-1, -1, -1):
			for i, node in enumerate(routes[root]):
				if routes[leaf][-1][1] == node[0]:
					add = routes[root][i:]
					one_of_routes = routes[leaf]
					for ad in add:
						one_of_routes.append(ad)
					routes[leaf] = one_of_routes
	calculate_time(routes)

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
		for i in time_list:
			print(i)
		print("\n")

import_time_table()
#print(time_table)
#print(arrive_table)
for goal in goal_stations:
	last_arrive = 2600
	calculate_last_train(goal)
	routes.append(one_of_routes)
	print(one_of_routes)
	print_routes(routes)
	branch_stations = double_check(branch_stations)
	one_of_routes = []
	another_route(branch_stations)
	print(one_of_routes)
	print("\n")
	routes = []
	used = []

