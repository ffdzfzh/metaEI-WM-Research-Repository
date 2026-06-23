# 此程序为使用RIS的计算覆盖图
# 同时指定RIS的类型，指定单目标、多目标还是混沌编码
# 注意transform_to_ris_coordinates要随着RIS的情况而随时更改
# 具体参照../Coding/Position_calculation.py中的设置

import json
import random
random.seed(42)
import cmath
from scipy import integrate
from scipy.special import fresnel
from scipy.spatial import distance
from collections import defaultdict
import nimbusrt as nrt
import nimbusrt.io as io
import numpy as np
import open3d as o3d
import pyvista as pv
import time
import math
import pickle
import os
from pyvistaqt import BackgroundPlotter
import matplotlib.pyplot as plt

# 定义常量
fc_value = 5.0e9  # 设置频率
c = 299792458  # 光速
lamda = c / fc_value
lamda_ = 1 / lamda  # 波长倒数
# RIS参数设置
lx, ly = 15, 14  # 阵列尺寸
wgts = np.ones((lx, ly))  # 权重矩阵（默认为全1）
reflect_amp = np.ones((lx, ly))  # 反射单元的幅度（默认为全1）
unitlength = lamda / 2  #
k = 2 * np.pi / lamda  # 波数
q_f, q_p = 2, 2  # 馈源和单元方向图的余弦指数
q_visual = 4
# 方向图参数
theta_numpts, phi_numpts = 91, 361  # 角度采样点数
theta_vec = np.linspace(0, 90, theta_numpts)  # 观察角：极角
phi_vec = np.linspace(0, 360, phi_numpts)  # 观察角：方位角
theta_mat, phi_mat = np.meshgrid(theta_vec, phi_vec)

xpos_vec = (np.arange(1, lx + 1) - (lx + 1) / 2) * unitlength
ypos_vec = (np.arange(1, ly + 1) - (ly + 1) / 2) * unitlength


def cartesian_to_angles(x, y, z):
    """三维坐标转极角(0-180°)和方位角(0-360°)"""
    # 计算球半径
    r = math.sqrt(x ** 2 + y ** 2 + z ** 2)
    # 处理原点特殊情况
    if r == 0:
        return 0, 0
    # 计算极角 (0°~180°)
    theta = math.degrees(math.acos(z / r))
    # 计算方位角 (0°~360°)
    phi = math.degrees(math.atan2(y, x))
    if phi < 0:
        phi += 360
    return theta, phi


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

    coeff = abs(cs**2)  # 功率算法
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


# # 一些坐标转换
# def transform_to_ris_coordinates(pos: np.ndarray, ris_center: np.ndarray) -> np.ndarray:
#     translated = pos - ris_center
#     # rotated = np.array([translated[1], translated[2], translated[0]])
#     rotated = np.array([translated[0], translated[2], -translated[1]])
#     return rotated


def cartesian_to_spherical_angles_deg(pos_local: np.ndarray):
    """
    输入为 RIS 坐标系下的点坐标 (x, y, z)
    返回 (distance, elevation_deg, azimuth_deg)
    elevation: arccos(z / r) in degrees
    azimuth: atan2(y, x) in degrees
    """
    x, y, z = pos_local
    r = np.sqrt(x**2 + y**2 + z**2)
    if r == 0:
        # 退化保护
        return 0.0, 0.0, 0.0
    elevation = np.degrees(np.arccos(z / r))
    azimuth = np.degrees(np.arctan2(y, x))
    return r, elevation, azimuth


def ris_incident_scatter_angles(source_pos, target_pos, ris_center):
    """
    给定 RIS 的 source/target 世界坐标，和 ris_corners，返回
    (theta_tx_deg, phi_tx_deg, theta_rx_deg, phi_rx_deg)
    """

    src_local = transform_to_ris_coordinates(np.asarray(source_pos, dtype=float), ris_center)
    tgt_local = transform_to_ris_coordinates(np.asarray(target_pos, dtype=float), ris_center)

    _, theta_tx_deg, phi_tx_deg = cartesian_to_spherical_angles_deg(src_local)
    _, theta_rx_deg, phi_rx_deg = cartesian_to_spherical_angles_deg(tgt_local)

    return theta_tx_deg, phi_tx_deg, theta_rx_deg, phi_rx_deg


# 从已有的方向图中进行增益采样
def calculate_radiation_pattern_sample(theta_tx_deg, phi_tx_deg, theta_rx_deg, phi_rx_deg, E_total):

    return 0

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


def calculate_tx_ris_rx_path_power(path_info, tx_pos, rx_pos, ris_center, E_total):
    """
    对单条 Tx→RIS→…→Rx 路径计算复增益：
    - 非 RIS 交互通过 modified_friis 得到幅度与相位
    - RIS 交互通过 calculate_radiation_pattern 得到 E_gain，并作为乘子
    返回 complex_gain
    """
    # 1) 构建路径点与交互系数
    path_points = [np.asarray(tx_pos, dtype=float)]
    reflection_coefficients = []
    diffraction_coefficients = []

    ris_E_gain = 1.0
    interaction_num = int(path_info.get("Interaction Num", 0))

    # 路径可能包含多个交互，第一类为 RIS，后续可能是反射/绕射
    # 严格按照 path_info 中的顺序构建 path_points
    for idx in range(interaction_num):
        inter_key = f"interaction {idx+1}"
        inter = path_info[inter_key]
        inter_type = inter.get("Type", None)

        # 记录交互点位置
        inter_pos = inter.get("Position", None)
        if inter_pos is None:
            raise ValueError(f"Path interaction {inter_key} missing Position.")
        path_points.append(np.asarray(inter_pos, dtype=float))

        if inter_type == "RIS":
            # 2) RIS 增益：从 Ris Source 和 Ris Target 计算角度并求 E_gain
            ris_source = np.asarray(path_info["Ris Source"], dtype=float)
            ris_target = np.asarray(path_info["Ris Target"], dtype=float)
            theta_tx_deg, phi_tx_deg, theta_rx_deg, phi_rx_deg = ris_incident_scatter_angles(
                ris_source, ris_target, ris_center
            )
            if theta_rx_deg >= 90:
                E_gain = 0  # 此处是为了解决内绕射会从RIS的侧面击中
            else:
                E_gain = E_total[round(phi_rx_deg)][round(theta_rx_deg)]
            ris_E_gain *= E_gain  # 该方向上的增益
            # 对 RIS 交互不加入反射/绕射系数
            reflection_coefficients.append(None)
            diffraction_coefficients.append(None)
        elif inter_type == "Reflection":
            reflection_coefficients.append(inter.get("Reflection Coefficient", None))
            diffraction_coefficients.append(None)
        elif inter_type == "Diffraction":
            reflection_coefficients.append(None)
            diffraction_coefficients.append(inter.get("Diffraction Coefficient", None))
        # else:
        #     # 未知类型，默认作为无额外系数的交互点
        #     reflection_coefficients.append(None)
        #     diffraction_coefficients.append(None)

    # 终点 Rx
    path_points.append(np.asarray(rx_pos, dtype=float))

    # 3) 非 RIS 部分用 modified_friis 得到路径功率增益与相位因子
    #    注意 modified_friis 内部应正确处理 None 的交互系数（按 1 或忽略）
    tx_to_rx_gain_linear, tx_to_rx_phase_factor = modified_friis(
        path_points, reflection_coefficients, diffraction_coefficients
    )

    # 4) 组合：复增益 = sqrt(功率增益) * 相位因子 * RIS E_gain
    complex_gain = np.sqrt(tx_to_rx_gain_linear) * tx_to_rx_phase_factor * ris_E_gain
    return complex_gain


# 批量计算：Tx→RIS→Rx 所有路径的接收功率
def compute_rx_gains_via_ris(all_path_info_TxRISsRxs, tx_positions, receiver_points, ris_center, E_total):
    """
    all_path_info_TxRISsRxs 的层级：
      all_path_info_TxRISsRxs[tx_idx][rx_idx] -> list_of_ris_groups
      其中每个 ris_group 是 “经若干 RIS 的一组路径”，
      ris_group[i] 是一条具体的路径字典（包含 Ris Source/Target 与若干 interaction）

    若你的结构是 “每个 rx 下有若干个 RIS（如 1 个或多个），
    每个 RIS 下有若干条路径”，此函数将对所有路径求和（复叠加）。

    返回：
      rx_gains2: dict{tuple(rx_pos): power_linear}
    """
    rx_gains2 = {}

    for tx_idx, tx_pos in enumerate(tx_positions):
        tx_pos = np.asarray(tx_pos, dtype=float)
        tx_to_all_rxs = all_path_info_TxRISsRxs[tx_idx]

        for rx_idx, path_groups in enumerate(tx_to_all_rxs):
            rx_pos = np.asarray(receiver_points[rx_idx], dtype=float)
            total_complex_sum = 0.0 + 0.0j

            # path_groups: list of groups, each group is a list of path_info dicts
            # 例如：path_groups[g] -> [path_dict_1, path_dict_2, ...]
            for group in path_groups:
                # group 可能已经是列表（多条路径），也可能就是单条路径字典
                if isinstance(group, dict):
                    group = [group]

                for path_info in group:
                    complex_gain = calculate_tx_ris_rx_path_power(
                        path_info, tx_pos, rx_pos, ris_center, E_total
                    )
                    total_complex_sum += complex_gain

            rx_power = np.abs(total_complex_sum) ** 2
            rx_gains2[tuple(rx_pos)] = rx_power

    return rx_gains2


# 叠加 rx_gains1 与 rx_gains2（同一 Rx 位置键）
def merge_rx_gains(rx_gains1: dict, rx_gains2: dict):
    """
    对同一接收点位置键（tuple(rx_pos)）的功率进行线性叠加：
    注意这里是不同“子系统”（Tx→Rx 与 Tx→RIS→Rx）之间的功率叠加，
    若需要全路径的相干叠加，应在更上层统一做复包络叠加。
    """
    rx_gains = defaultdict(float)
    for k, v in rx_gains1.items():
        rx_gains[k] += v
    for k, v in rx_gains2.items():
        rx_gains[k] += v
    return dict(rx_gains)


def generate_receiver_grid(corners, rows, cols, space_u, space_v):
    """
    将四边形面划分为rows×cols的网格，返回每个网格点的中心坐标
    corners: 四个角点坐标，顺序为左下、左上、右上、右下
    """
    # 将输入点转换为numpy数组
    p1, p2, p3, p4 = [np.array(p) for p in corners]

    # 验证输入点是否形成平面四边形
    if not np.allclose(p2 - p1 - (p3 - p4), np.zeros(3)):
        raise ValueError("Input points do not form a valid quadrilateral plane")

    # 生成网格点
    grid_points = []
    for i in range(rows):
        for j in range(cols):
            # 在u和v方向上的参数
            u = (j + space_u) / cols
            v = (i + space_v) / rows

            # 双线性插值计算网格点坐标
            point = (1 - u) * (1 - v) * p1 + (1 - u) * v * p2 + u * v * p3 + u * (1 - v) * p4
            grid_points.append(point)

    return grid_points


# 坐标转换
def transform_to_ris_coordinates(pos, ris_center):
    pos = np.array(pos)
    ris_center = np.array(ris_center)
    translated = pos - ris_center
    # # RIS的y坐标不变
    # if pos.ndim == 1:
    #     return np.array([translated[0],  translated[2], -translated[1]])
    # else:
    #     ris_coords = np.empty_like(translated)
    #     ris_coords[:, 0] = translated[:, 0]  # 保留x
    #     ris_coords[:, 1] = translated[:, 2]  # z -> y
    #     ris_coords[:, 2] = -translated[:, 1]  # -y -> z

    # RIS的x坐标不变
    if pos.ndim == 1:
        return np.array([translated[1],  translated[2], translated[0]])
    else:
        ris_coords = np.empty_like(translated)
        ris_coords[:, 0] = translated[:, 1]
        ris_coords[:, 1] = translated[:, 2]
        ris_coords[:, 2] = translated[:, 0]
    return ris_coords


# 根据编码计算RIS方向图函数
def calculate_radiation_pattern(theta_vec, phi_vec, coding, tx_virtual, ris_center):
    # 创建二维网格矩阵
    theta_mat, phi_mat = np.meshgrid(theta_vec, phi_vec)
    theta_rad = np.deg2rad(theta_mat)  # 转换为弧度
    phi_rad = np.deg2rad(phi_mat)  # 转换为弧度

    # 方向余弦
    u = np.sin(theta_rad) * np.cos(phi_rad)
    v = np.sin(theta_rad) * np.sin(phi_rad)
    w = np.cos(theta_rad)

    # 发射图
    # mask = (theta_rad >= 0) & (theta_rad <= np.pi / 2)
    # e_obs = np.where(mask, np.cos(theta_rad) ** 2, 0)
    e_obs = 1  # 为等效源发射方向图，按照全向天线处理

    # 对RIS平面与虚拟源坐标完成坐标转换
    # ris_points = transform_to_ris_coordinates(ris_points, ris_center)
    tx_virtual = transform_to_ris_coordinates(tx_virtual, ris_center)

    # 初始化方向图
    E = np.zeros_like(theta_mat, dtype=complex)

    # 遍历阵列单元
    for m in range(lx):
        for n in range(ly):
            # 转换后单元位置
            # rmn = ris_points[m * ly + n]
            xm = xpos_vec[m]
            ym = ypos_vec[n]
            rmn = np.array([xm, ym, 0])
            # 馈源到单元的距离向量
            rfm = rmn - np.array(tx_virtual)
            rfm_norm = np.linalg.norm(rfm)
            theta_f = np.arccos(np.dot(rfm, -np.array(tx_virtual)) / (rfm_norm * np.linalg.norm(tx_virtual)))
            ef_theta_f = np.cos(theta_f) ** q_f if 0 <= theta_f <= np.pi / 2 else 0  # 馈源方向图
            theta_p = np.arccos(np.dot(rfm, np.array([0, 0, -1])) / rfm_norm)
            ee_theta_p = np.cos(theta_p) ** q_p if 0 <= theta_p <= np.pi / 2 else 0  # 离散单元方向图

            # 计算相位延迟
            phase_shift = k * (rmn[0] * u + rmn[1] * v - rfm_norm) + coding[n, m] * np.pi
            # phase_shift = k * (xm * u + ym * v)
            # # 提前归一化
            # E_norm = np.linalg.norm(rfm - np.array(tx_virtual))
            # 叠加辐射场
            E += wgts[m, n] * reflect_amp[m, n] * ef_theta_f * ee_theta_p * e_obs * np.exp(1j * phase_shift)
            # E += wgts[m, n] * reflect_amp[m, n] * np.exp(1j * phase_shift)

    return np.abs(E) / np.max(abs(E)), np.max(abs(E))


def read_3d_coordinates_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        coordinates = json.load(file)
    return coordinates


def load_from_json(filename):
    """从 JSON 加载数据"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"数据已从 {filename} 加载")
    return data


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
    # scene1场景为先计算各个发射机和接收机没有经过RIS的情况
    scene1 = nrt.Scene()
    file = "data_all\scene_show\scene1.ply"
    scene1.set_point_cloud(file)
    type = "data_all\scene_show\scene1.txt"
    scene1.set_EM_mapping(type)
    scene1.add_edges(scene1.read_edges_from_json("data_all\scene_show\scene1.ply"))
    # tx_pos = [8.028, 0, 0.5]
    tx_pos = [3, -5, 1.2]
    tx_key = 'tx0'
    scene1.add_transmitter(tx_key, tx_pos)  # 52.88655491	65.71758092	10

    # 生成接收点
    # 这里的接收点指的是需要计算覆盖图的接收点
    inside_file = "data_all\scene_show\scene1_inside_points.json"
    receiver_points = read_3d_coordinates_from_json(inside_file)
    # rx_num = len(receiver_points)
    # receiver_points = [[2.52488, -6.09322, 1.5]]

    # 将所有接收机加入scene中
    for i, receiver in enumerate(receiver_points):
        rx_key = f"rx{i}"
        scene1.add_receiver(rx_key, receiver)

    # 在数据处理中将打在RIS上的射线删去
    # 定义RIS的四个角点
    ris_corners = [
        [2.1, -4.4, 1.15],  # 左下
        [2.1, -4.4, 1.79],  # 左上
        [2.1, -4.76, 1.79],  # 右上
        [2.1, -4.76, 1.15]  # 右下
    ]
    # ris_corners = [
    #     [9.2, 1.8, 0.2],
    #     [9.2, 1.8, 0.84],
    #     [9.84, 1.8, 0.84],
    #     [9.84, 1.8, 0.2]
    # ]
    ris_corners_tmp = np.array(ris_corners)
    ris_center = (ris_corners_tmp[0] + ris_corners_tmp[1] + ris_corners_tmp[2] + ris_corners_tmp[3]) / 4
    ris_enabled = True

    # 单元间距与厚度
    space_u = space_v = 0.5  # 这个不用改，就是0.5
    thickness = 0.1
    # 定义接受面厚度，以检测非RIS射线是否被面遮挡住
    # 这里是非常简单的情况，如果非平行于轴的话可以直接以点的坐标代替
    tolerance = thickness / 2
    receiver_x = ris_corners[0][0]
    y_coords = [corner[1] for corner in ris_corners]
    z_coords = [corner[2] for corner in ris_corners]
    min_y = min(y_coords)
    max_y = max(y_coords)
    min_z = min(z_coords)
    max_z = max(z_coords)
    min_x = receiver_x - tolerance
    max_x = receiver_x + tolerance

    # 生成64个接收点
    ris_points = generate_receiver_grid(ris_corners, lx, ly, space_u, space_v)

    coding = np.load("Coding/coding_npy/coding_focus2.npy", allow_pickle=True)
    E, max_E = calculate_radiation_pattern(theta_vec, phi_vec, coding, tx_pos, ris_center)
    E_total = lx * ly * max_E * E * 0.25
    # E_total = calculate_radiation_pattern(theta_vec, phi_vec, coding, tx_pos, ris_center)
    # 不考虑打在RIS上的射线考虑三次反射一次绕射
    scene1.compute_paths(reconstructed_corridor_input_params(num_interactions=3, num_diffractions=1))

    # 处理路径数据
    paths = scene1.path_storage._paths

    all_path_info_TxRxs = []
    for index, receiver in enumerate(receiver_points):
        rx_key = f"rx{index}"
        all_path_info_TxRx = []
        if tx_key in paths and rx_key in paths[tx_key]:
            path_array = paths[tx_key][rx_key]
            print(f"Found {len(path_array)} paths from {tx_key} to {rx_key}.")
            for i, path in enumerate(path_array):
                path_data = {
                    "Time Delay": path.time_delay,
                    "Interaction Num": len(path.interactions),
                    "LOS": None,

                    "Ris Enabled": None,
                    "Ris Source": None
                }


                if len(path.interactions) == 0:
                    path_data["LOS"] = 1

                points = []
                coefficients = []  # 存储每个交互点的反射或绕射系数
                flag_tmp = False
                for j, interaction in enumerate(path.interactions):
                    position = interaction.position.tolist() if hasattr(interaction.position, 'tolist') else interaction.position

                    # 先检测是否与RIS交互，交互直接跳出循环
                    # 这里只是简单情况的立方体，如果有更为复杂的RIS阵列需要改动
                    # 这里需要改进！！或者直接在场景中加入RIS
                    x_tmp, y_tmp, z_tmp = position
                    flag_tmp = (min_x <= x_tmp <= max_x and min_y <= y_tmp <= max_y and min_z <= z_tmp <= max_z)
                    if flag_tmp and ris_enabled:
                        break

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
                    # position = interaction.position
                    # normal = interaction.normal
                    # interaction_type = str(interaction.type)

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
                        # eta_r = 5

                        reflection_coefficient = reflection_coeff(theta_i, eta_r, fc_value)
                        interaction_data["Reflection Coefficient"] = reflection_coefficient
                        # diffraction_coefficient = None

                    elif interaction_type.endswith('.DIFFRACTION'):
                        # interaction_type = '绕射'
                        interaction_data["Type"] = "Diffraction"
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
                        # eta_0 = 5
                        # eta_n = 5

                        diffraction_coefficient = diffraction_coeff(edge.n, d_dash, d, phi_dash, phi, eta_0, eta_n, fc_value)
                        # reflection_coefficient = None
                        interaction_data["Diffraction Coefficient"] = diffraction_coefficient

                    path_data[f"interaction {j + 1}"] = interaction_data
                # 如果接收点没有打到RIS上才被接收
                if not flag_tmp:
                    all_path_info_TxRx.append(path_data)
        else:
            print(f"No paths found from {tx_key} to {rx_key}.")
        all_path_info_TxRxs.append(all_path_info_TxRx)

    # =============至此，Tx-Rxs并且不经RIS的路径已经被处理完，存在all_path_info_TxRxs变量中=============

    # coding直接由Coding中编码的各个程序给出，并保存在Coding/coding_npy下
    # coding = np.load("Coding/coding_npy/coding_focus1.npy", allow_pickle=True)
    # E_total = calculate_radiation_pattern(theta_vec, phi_vec, coding, tx_pos, ris_points, ris_center)
    # 开始处理RIS路径,这里需要重新定义scene

    rx_gains1 = {}
    for unit, path_datas in enumerate(all_path_info_TxRxs):
        rx_pos = receiver_points[unit]
        all_gain = 0
        for path_index, path_data in enumerate(path_datas):
            gain_tx_rx = calculate_tx_rx_path_power(path_data, tx_pos, rx_pos)
            all_gain += gain_tx_rx
        all_power = abs(all_gain ** 2)
        rx_gains1[tuple(rx_pos)] = all_power

    rx_gains2 = compute_rx_gains_via_ris(
        all_path_info_TxRISsRxs=all_path_info_TxRISsRxs,
        tx_positions=[tx_pos],
        receiver_points=receiver_points,
        ris_center=ris_center,
        E_total=E_total)

    # # 总功率叠加
    # rx_gains = merge_rx_gains(rx_gains1, rx_gains2)
    # with open("data_all\scene_show\inside_power_ris.pkl", "wb") as f:  # 二进制写入模式
    #     pickle.dump(rx_gains, f)
