import argparse
import logging
from pathlib import Path

import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd


def buildGraph(G, tuple):
    # 为边添加属性
    G.add_edge(tuple[0], tuple[2], type=tuple[1], condition=tuple[4], purpose=tuple[5])
    if tuple[3] != 'none':
        G.add_edge(tuple[2], tuple[3])


def showGraph(G):
    # 可视化图形
    pos = nx.spring_layout(G)  # 为图形设置布局
    plt.figure(figsize=(80, 80))
    nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='k', node_size=1500)

    # 定义要打印的属性
    attributes = ['type', 'condition', 'purpose']

    # 获取边的属性并打印
    edge_labels = {(u, v): ', '.join(f"{key}: {data[key]}" for key in attributes if key in data)
                   for u, v, data in G.edges(data=True)}

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # 显示图形
    plt.show()




def main():
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--Name", help="Name")
    args = parser.parse_args()

    name = Path(args.Name)

    # 创建一个有向无环图
    G = nx.DiGraph()

    # 打开CSV文件
    with open(f'./Tuples/{name}.csv', mode='r', encoding='utf-8') as file:
        for line in file:
            line = line.strip('\n').strip('<').strip('>')
            elements = line.split(';')
            # print(type(elements))
            elements = [element.strip() for element in elements]
            # print(elements)
            for i in range(3):
                if elements[i] == 'none':
                    continue
            buildGraph(G, elements)
            # break
            # print(line.strip('\n'))
    showGraph(G)


if __name__ == '__main__':
    main()
