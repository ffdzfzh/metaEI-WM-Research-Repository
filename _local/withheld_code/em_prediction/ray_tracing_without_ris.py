# 此程序为未使用RIS的计算覆盖图
import json
import random
import cmath
import pickle
from scipy import integrate
from scipy.special import fresnel
from scipy.spatial import distance
import nimbusrt as nrt
import nimbusrt.io as io
import numpy as np
import open3d as o3d
import pyvista as pv
import time
import os
from pyvistaqt import BackgroundPlotter
import matplotlib.pyplot as plt

fc_value = 5.0e9  # 设置频率
c = 299792458  # 光速
lamda = c / fc_value
lamda_ = 1 / lamda  # 波长倒数


def transition_f(X):
    # UTD理论中F函数的近似求解
    if X <= 0.3:
        term1 = cmath.sqrt(np.pi * X)
        term2 = 2 * X * cmath.exp(1j * np.pi / 4)
        term3 = (2 / 3) * X ** 2 * cmath.exp(-1j * np.pi / 4)
        f = (term1 - term2 - term3) * cmath.exp(1j * (np.pi / 4 + X))
    elif X >= 5.5:
        term1 = 1
        term2 = 1j * (1 / (2 * X))
        term3 = -(3 / 4) * (1 / X ** 2)
        term4 = -1j * (15 / 8) * (1 / X ** 3)
        term5 = (75 / 16) * (1 / X ** 4)
        term6 = -1j * (375 / 32) * (1 / X ** 4)
        f = term1 + term2 + term3 + term4 + term5 + term6
    else:
        sqrt_X = np.sqrt(X)
        sqrt_pi_half = np.sqrt(np.pi / 2)
        S, C = fresnel(sqrt_X / sqrt_pi_half)
        integral = (C - 1 + 1j * (S - 1)) * sqrt_pi_half
        f = 2 * 1j * sqrt_X * np.exp(1j * X) * integral

    return f


def diffraction_coeff(n, d_dash, d, phi_dash, phi, eta_0, eta_n, f) -> complex:
    # 计算绕射系数 D 的值
    # 仅考虑垂直极化波
    c = 299792458  # 光速
    lamda = c / f  # 波长
    k = 2 * np.pi / lamda  # 波数
    L = (d_dash * d) / (d_dash + d)  # 基线距离-球面波
    A = -np.exp(-1j * np.pi / 4) / (2 * n * np.sqrt(2 * np.pi * k))
    gamma1 = (np.pi - (phi - phi_dash)) / (2 * n)
    gamma2 = (np.pi + (phi - phi_dash)) / (2 * n)
    gamma3 = (np.pi - (phi + phi_dash)) / (2 * n)
    gamma4 = (np.pi + (phi + phi_dash)) / (2 * n)

    D1 = A * (np.cos(gamma1) / np.sin(gamma1)) * transition_f(2 * k * L * n ** 2 * (np.sin(gamma1)) ** 2)
    D2 = A * (np.cos(gamma2) / np.sin(gamma2)) * transition_f(2 * k * L * n ** 2 * (np.sin(gamma2)) ** 2)
    D3 = A * (np.cos(gamma3) / np.sin(gamma3)) * transition_f(2 * k * L * n ** 2 * (np.sin(gamma3)) ** 2)
    D4 = A * (np.cos(gamma4) / np.sin(gamma4)) * transition_f(2 * k * L * n ** 2 * (np.sin(gamma4)) ** 2)

    theta_i = np.pi / 2 - phi_dash
    eta_r = eta_0
    R0 = (np.cos(theta_i) - np.sqrt(eta_r - np.sin(theta_i) ** 2)) / \
         (np.cos(theta_i) + np.sqrt(eta_r - np.sin(theta_i) ** 2))
    R0 = abs(R0)

    theta_r = abs(np.pi / 2 - (n * np.pi - phi))  # 注意这里，有可能phi比较小，在0面一侧

    eta_r = eta_n
    Rn = (np.cos(theta_r) - np.sqrt(eta_r - np.sin(theta_r) ** 2)) / \
         (np.cos(theta_r) + np.sqrt(eta_r - np.sin(theta_r) ** 2))
    Rn = abs(Rn)

    D0 = D1 + D2 + R0 * D3 + Rn * D4
    # D = abs(D0) * np.sqrt((d_dash + d) / (d_dash * d))
    # D = abs(D0.real) * np.sqrt((d_dash + d) / (d_dash * d))

    D = abs(D0 ** 2)
    # D = D0  # 幅度算法

    return D


def reflection_coeff(theta_i, eta_r, fc) -> complex:
    # 求解反射系数
    # 仅考虑垂直极化波
    delta_h = 0.0025  # 这个参数定义看论文A Hybrid Millimeter-wave Channel Simulator for Joi
    c = 299792458
    lamda = c / fc

    cs = np.cos(theta_i) - np.sqrt(eta_r - np.sin(theta_i) ** 2) / (
            np.cos(theta_i) + np.sqrt(eta_r - np.sin(theta_i) ** 2))
    # rho_s = np.exp(-8 * (np.pi * delta_h * np.cos(theta_i) / lamda) ** 2)
    # coeff = ((1 + rho_s) / 2) * abs(cs)

    coeff = abs(cs ** 2)  # 功率算法
    # coeff = cs  # 幅度算法

    return coeff


def calculate_phase_factor(distance, lamda_=lamda_):
    """
    根据距离计算相位因子
    """
    phase_shift = 2 * np.pi * lamda_ * distance
    return np.exp(1j * phase_shift)


def friis_equation(distance, wavelength=lamda):
    """
    使用弗里斯公式计算自由空间路径损耗
    """
    return (wavelength / (4 * np.pi * distance)) ** 2  # 功率算法
    # return wavelength / (4 * np.pi * distance)  # 幅度算法


def modified_friis(path_points, reflection_coefficients, diffraction_coefficients):
    """
    包含反射/绕射的修正弗里斯公式
    参数:
    path_points -- 路径点列表 [发射机, 交互点1, 交互点2, ..., 接收机]
    reflection_coefficients -- 反射系数平方值
    diffraction_coefficients -- 绕射系数平方值
    """
    total_gain = 1.0  # 包含初始功率幅度！以及所有增益计算，这里简化为1
    tmp = 0.0
    # 计算每段路径的弗里斯增益并累积
    for i in range(len(path_points) - 1):
        segment_start = np.array(path_points[i])
        segment_end = np.array(path_points[i + 1])
        distance = np.linalg.norm(segment_end - segment_start)
        tmp += distance
        segment_gain = friis_equation(distance)
        total_gain *= segment_gain

        # 如果是反射或绕射，在对应位置应用衰减系数
        if i < len(reflection_coefficients) and reflection_coefficients[i] is not None:
            total_gain *= reflection_coefficients[i]
        elif i < len(diffraction_coefficients) and diffraction_coefficients[i] is not None:
            total_gain *= diffraction_coefficients[i]
    phase_factor = calculate_phase_factor(tmp)
    return total_gain, phase_factor


def calculate_tx_rx_path_power(path_info, tx_pos, rx_pos):

    # 构建发射机到rx的路径
    path_points = [tx_pos]
    reflection_coefficients = []
    diffraction_coefficients = []

    # 添加交互点
    for index in range(path_info["Interaction Num"] - 1):
        interaction = path_info["interaction " + str(index + 1)]
        path_points.append(interaction["Position"])
        reflection_coefficients.append(interaction["Reflection Coefficient"])
        diffraction_coefficients.append(interaction["Diffraction Coefficient"])

    # 计算发射机到RIS的增益
    path_points.append(rx_pos)
    tx_to_rx_gain, tx_to_rx_phase_factor = modified_friis(path_points, reflection_coefficients, diffraction_coefficients)

    # 应用相位因子
    # phase_factor = calculate_phase_factor(path_info["Time Delay"])  # 这个时延有点抽象
    complex_gain = np.sqrt(tx_to_rx_gain) * tx_to_rx_phase_factor   # 间接幅度算法
    # complex_gain = total_gain * phase_factor * ris_gain  # 直接幅度算法
    return complex_gain  # 返回幅度


def read_3d_coordinates_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        coordinates = json.load(file)
    return coordinates


def reconstructed_corridor_input_params(num_interactions=2, num_diffractions=1):
    input_data = nrt.InputData()
    input_data.scene_settings.frequency = fc_value  # 射线追踪频率
    # input_data.scene_settings.voxel_size = 0.5  # 体素的大小
    input_data.scene_settings.voxel_size = 0.5  # 体素的大小
    input_data.scene_settings.voxel_division_factor = 2  # 体素划分因子
    input_data.scene_settings.subvoxel_division_factor = 4  # 子体素划分因子
    input_data.scene_settings.received_path_buffer_size = 25000
    input_data.scene_settings.propagation_path_buffer_size = 100000
    # input_data.scene_settings.received_path_buffer_size = 500000
    # input_data.scene_settings.propagation_path_buffer_size = 2000000
    input_data.scene_settings.propagation_buffer_size_increase_factor = 2.0
    input_data.scene_settings.sample_radius_coarse = 0.015
    # input_data.scene_settings.sample_radius_refine = 0.01
    input_data.scene_settings.sample_radius_refine = 0.003
    input_data.scene_settings.variance_factor_coarse = 2.0
    input_data.scene_settings.variance_factor_refine = 2.0
    # input_data.scene_settings.sdf_threshold_coarse = 0.0015
    # input_data.scene_settings.sdf_threshold_refine = 0.0005
    input_data.scene_settings.sdf_threshold_coarse = 0.0015
    input_data.scene_settings.sdf_threshold_refine = 0.0005
    input_data.scene_settings.num_iterations = 2000
    input_data.scene_settings.delta = 1e-4
    input_data.scene_settings.alpha = 0.4
    input_data.scene_settings.beta = 0.4
    input_data.scene_settings.angle_threshold = 1.0
    input_data.scene_settings.distance_threshold = 0.02
    # input_data.scene_settings.angle_threshold = 25
    # input_data.scene_settings.distance_threshold = 0.02
    input_data.scene_settings.block_size = 32
    input_data.scene_settings.num_coarse_paths_per_unique_route = 100
    input_data.num_interactions = num_interactions
    input_data.num_diffractions = num_diffractions
    return input_data


if __name__ == "__main__":

    scene = nrt.Scene()
    file = "data_all\scene_show\scene1.ply"
    scene.set_point_cloud(file)
    type = "data_all\scene_show\scene1.txt"
    scene.set_EM_mapping(type)
    scene.add_edges(scene.read_edges_from_json("data_all\scene_show\scene1.ply"))
    tx_pos = [3, -5, 1.2]
    tx_key = 'tx0'
    scene.add_transmitter(tx_key, tx_pos)  # 52.88655491	65.71758092	10

    # 生成接收点
    inside_file = "data_all\scene_show\scene1_inside_points.json"
    receiver_points = read_3d_coordinates_from_json(inside_file)

    # 将所有接收机加入scene中
    for i, receiver in enumerate(receiver_points):
        rx_key = f"rx{i}"
        scene.add_receiver(rx_key, receiver)

    # 计算传播路径
    scene.compute_paths(reconstructed_corridor_input_params(num_interactions=3, num_diffractions=1))
    # 处理路径数据
    paths = scene.path_storage._paths

    all_path_info_TxRxs = []
    for index, receiver in enumerate(receiver_points):
        rx_key = f"rx{index}"
        all_path_info = []
        if tx_key in paths and rx_key in paths[tx_key]:
            path_array = paths[tx_key][rx_key]
            # print(f"Found {len(path_array)} paths from {tx_key} to {rx_key}.")
            for i, path in enumerate(path_array):
                path_data = {
                    "Time Delay": path.time_delay,
                    "Interaction Num": len(path.interactions),
                    "LOS": None,
                    "Ris Enabled": 1,
                    "Ris Source": None
                }

                if len(path.interactions) == 0:
                    path_data["LOS"] = 1

                points = []
                coefficients = []  # 存储每个交互点的反射或绕射系数

                for j, interaction in enumerate(path.interactions):
                    position = interaction.position.tolist() if hasattr(interaction.position, 'tolist') else interaction.position
                    normal = interaction.normal.tolist() if hasattr(interaction.normal, 'tolist') else interaction.normal
                    interaction_type = str(interaction.type)

                    # if j + 1 == len(path.interactions):
                    #     path_data["Ris Source"] = position

                    interaction_data = {
                        "Position": position,
                        "Normal": normal,
                        "Type": None,
                        "Reflection Coefficient": None,
                        "Diffraction Coefficient": None
                    }

                    if interaction_type.endswith('.REFLECTION'):
                        interaction_data["Type"] = "Reflection"
                        # interaction_type = '反射'

                        # 计算入射角theta_i（示例计算）
                        prev_point = path.interactions[j - 1].position if j > 0 else tx_pos
                        # incident_vector = position - prev_point
                        # incident_vector = [position[pos] - prev_point[pos] for pos in range(3)]
                        incident_vector = [prev_point[pos] - position[pos] for pos in range(3)]
                        incident_vector = np.array(incident_vector)
                        incident_vector /= np.linalg.norm(incident_vector)
                        cos_theta_i = np.dot(normal, incident_vector)  # 计算入射角的余弦值
                        theta_i = np.arccos(abs(cos_theta_i))  # 计算入射角

                        eta_r = random.uniform(4, 6)  # 随机生成介电常数

                        reflection_coefficient = reflection_coeff(theta_i, eta_r, fc_value)
                        interaction_data["Reflection Coefficient"] = reflection_coefficient
                        # diffraction_coefficient = None

                    elif interaction_type.endswith('.DIFFRACTION'):
                        # interaction_type = '绕射'
                        interaction_data["Type"] = "Diffraction"
                        flag = 1
                        edge = interaction.edge

                        # 计算d_dash和d
                        prev_point = path.interactions[j - 1].position if j > 0 else tx_pos
                        next_point = path.interactions[j + 1].position if j < len(path.interactions) - 1 else receiver
                        # d_dash = np.linalg.norm(position - prev_point)
                        d_dash = distance.euclidean(prev_point, position)
                        # d = np.linalg.norm(next_point - position)
                        d = distance.euclidean(next_point, position)

                        # 计算phi_dash和phi
                        face0_normal = edge.edge_face0.normal
                        # face1_normal = edge.edge_face1.normal

                        # incident_vector = position - prev_point
                        incident_vector = [prev_point[pos] - position[pos] for pos in range(3)]
                        incident_unit = incident_vector / np.linalg.norm(incident_vector)
                        phi_dash = np.pi / 2 - np.arccos(np.dot(face0_normal, incident_unit))

                        # outgoing_vector = next_point - position
                        # outgoing_vector = position - next_point
                        outgoing_vector = [position[pos] - next_point[pos] for pos in range(3)]
                        outgoing_unit = outgoing_vector / np.linalg.norm(outgoing_vector)
                        phi = np.arccos(np.dot(face0_normal, outgoing_unit)) + np.pi / 2

                        eta_0 = random.uniform(4, 6)  # 随机生成介电常数
                        eta_n = random.uniform(4, 6)  # 随机生成介电常数

                        diffraction_coefficient = diffraction_coeff(edge.n, d_dash, d, phi_dash, phi, eta_0, eta_n, fc_value)
                        # reflection_coefficient = None
                        interaction_data["Diffraction Coefficient"] = diffraction_coefficient

                    path_data[f"interaction {j + 1}"] = interaction_data

                all_path_info.append(path_data)
        all_path_info_TxRxs.append(all_path_info)

    rx_gains = {}
    for unit, path_datas in enumerate(all_path_info_TxRxs):
        rx_pos = receiver_points[unit]
        all_gain = 0
        for path_index, path_data in enumerate(path_datas):
            gain_tx_rx = calculate_tx_rx_path_power(path_data, tx_pos, rx_pos)
            all_gain += gain_tx_rx
        all_power = abs(all_gain ** 2)
        rx_gains[tuple(rx_pos)] = all_power
        # print(all_power)

    # 保存为字典
    # with open("data_all\scene_show\inside_power.pkl", "wb") as f:  # 二进制写入模式
    #     pickle.dump(rx_gains, f)

