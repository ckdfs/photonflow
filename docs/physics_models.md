# 物理模型与公式推导说明

本文件描述核心器件的物理模型与关键公式，使用 LaTeX 表达式。

## 记号约定
- $j = \sqrt{-1}$
- 光学复包络：$E(t)$
- 物理场：$\Re\{E(t)\,e^{j2\pi f_0 t}\}$
- 双偏振：$E(t)$ 为 $2\times 1$ Jones 向量 $[E_x(t), E_y(t)]^T$

<a id="laser"></a>
## 激光器
基础光场：

$$
E_{\mathrm{in}}(t) = \sqrt{P(t)}\,\exp\left(j\left(2\pi f_0 t + \phi_L(t)\right)\right)
\tag{LASER-1}
$$

线宽相位噪声：

$$
\phi_L(t+\Delta t) = \phi_L(t) + \sqrt{2\pi\Delta f\,\Delta t}\;w(t)
\tag{LASER-2}
$$

其中 $w(t)\sim\mathcal{N}(0,1)$。

RIN（相对强度噪声）：

$$
P(t) = P_0\left(1 + n_{\mathrm{RIN}}(t)\right)
\tag{LASER-3}
$$

$n_{\mathrm{RIN}}(t)$ 的功率谱由 RIN 指标设定。

非理想补充：
- 功率误差（dB）：$E \leftarrow E \cdot 10^{\Delta P_{\mathrm{dB}}/20}$
- 频偏：$f_0 \leftarrow f_0 + \Delta f$
- 额外相位抖动：$\phi_L(t) \leftarrow \phi_L(t) + \sigma_\phi\,w(t)$

<a id="pm"></a>
## 相位调制器（PM）
理想 PM：

$$
E_{\mathrm{out}}(t) = E_{\mathrm{in}}(t)\,\exp\left(j\phi(t)\right)
\tag{PM-1}
$$

$$
\phi(t) = \phi_{\mathrm{bias}} + \pi\,\frac{V(t)}{V_{\pi}}
\tag{PM-2}
$$

单音驱动（$V(t)=V_{\mathrm{pk}}\sin(2\pi f_m t)$）：

$$
m = \pi\frac{V_{\mathrm{pk}}}{V_{\pi}}
$$

$$
E_{\mathrm{out}}(t) = E_0 e^{j2\pi f_0 t} e^{jm\sin(2\pi f_m t)}
$$

$$
e^{jm\sin x} = \sum_{n=-\infty}^{\infty} J_n(m)\,e^{jnx}
\tag{PM-3}
$$

产生光学边带 $f_0 \pm n f_m$，幅度由 $J_n(m)$ 决定。

非理想项：
- 插入损耗：$E_{\mathrm{out}} \leftarrow E_{\mathrm{out}}\,10^{-L_{\mathrm{dB}}/20}$
- 带宽限制：$V(t) \leftarrow \mathcal{F}^{-1}\{\mathcal{F}\{V\}H(f)\}$
- $V_{\pi}$ 误差：$V_{\pi} \leftarrow V_{\pi}(1+\epsilon)$
- 驱动噪声：$V(t) \leftarrow V(t) + \sigma_V w(t)$
- 偏置误差：$\phi_{\mathrm{bias}} \leftarrow \phi_{\mathrm{bias}} + \Delta\phi$

带宽模型（可选）：
- 理想矩形低通：$H(f)=\mathbf{1}_{|f|\le f_c}$
- 一阶 RC：$H(f)=\frac{1}{1+j f/f_c}$
\tag{LP-1}

<a id="attenuator"></a>
## 光衰减器（Attenuator）
理想衰减：

$$
E_{\mathrm{out}}(t) = E_{\mathrm{in}}(t)\,10^{-L_{\mathrm{dB}}/20}
\tag{ATT-1}
$$

<a id="phase_shifter"></a>
## 相移器（PhaseShifter）
固定相移：

$$
E_{\mathrm{out}}(t) = E_{\mathrm{in}}(t)\,e^{j\phi}
\tag{PS-1}
$$

<a id="fiber"></a>
## 光纤（线性色散 + 损耗）
频域传输：

$$
E_{\mathrm{out}}(t) = \mathcal{F}^{-1}\left\{\mathcal{F}\{E_{\mathrm{in}}(t)\}\,H_{\mathrm{fiber}}(f)\right\}
\tag{FIBER-1}
$$

$$
H_{\mathrm{fiber}}(f)=10^{-\alpha_{\mathrm{dB}}\,(L/1000)/20}\,
\exp\left(j\left(-\frac{1}{2}\beta_2 L \omega^2-\frac{1}{6}\beta_3 L \omega^3\right)\right)
$$

其中 $\omega=2\pi f$，$L$ 为长度（m），$\alpha_{\mathrm{dB}}$ 为 dB/km 衰减系数。

SSFM 分步传播（对色散与非线性做分步近似）：

$$
E_{k+1} = \mathcal{L}_{\Delta z/2}\left(\mathcal{N}_{\Delta z}\left(\mathcal{L}_{\Delta z/2}(E_k)\right)\right)
\tag{FIBER-4}
$$

自动分步时，$\Delta z$ 由最大相位阈值与长度尺度共同约束：

$$
L_D \approx \frac{1}{|\beta_2|\omega_{\mathrm{rms}}^2},\quad L_{D3}\approx \frac{1}{|\beta_3|\omega_{\mathrm{rms}}^3},\quad
L_{NL}=\frac{1}{\gamma P_{\max}}
$$

$$
\Delta z \approx \min\left(\Delta z_{\phi},\,\eta\cdot\min(L_D,L_{D3},L_{NL})\right)
$$

其中 $\eta$ 为比例系数。

偏振模色散（PMD）与双折射：

$$
\mathbf{E}_{\mathrm{out}}(f)=R(-\theta)\,
\begin{bmatrix}e^{-j\phi/2} & 0 \\ 0 & e^{j\phi/2}\end{bmatrix}
R(\theta)\,\mathbf{E}_{\mathrm{in}}(f)
\tag{FIBER-2}
$$

$$
\phi(\omega)=\phi_b+\omega\,\tau_{\mathrm{DGD}}
$$

时变 PMD 采用分块更新：每个时间块内以不同参数应用同一 PMD 变换。

Kerr 非线性（简化 SPM）：

$$
E_{\mathrm{out}}(t)=E_{\mathrm{in}}(t)\exp\left(j\gamma L_{\mathrm{eff}}|E(t)|^2\right)
\tag{FIBER-3}
$$

$$
L_{\mathrm{eff}}=\frac{1-e^{-\alpha_p L}}{\alpha_p},\quad \alpha_p=\frac{\ln 10}{10}\frac{\alpha_{\mathrm{dB}}}{1000}
$$

双偏振时 $|E(t)|^2=|E_x|^2+|E_y|^2$。

<a id="optical_filter"></a>
## 光学滤波器（频域整形）

$$
E_{\mathrm{out}}(t) = \mathcal{F}^{-1}\left\{\mathcal{F}\{E_{\mathrm{in}}(t)\}\,H_{\mathrm{filter}}(f)\right\}
\tag{FILTER-1}
$$

常用响应：
- 矩形：$H(f)=\mathbf{1}_{|f-f_c|\le B/2}$
- 高斯：$H(f)=\exp\left(-\frac{1}{2}\left(\frac{f-f_c}{\sigma}\right)^2\right)$
- Butterworth：$H(f)=\left(1+(|f-f_c|/f_b)^{2n}\right)^{-1/2}$

相位/群时延模型：

$$
H(f)=|H(f)|\exp\left(-j\omega\tau - \frac{j}{2}\beta_2\omega^2\right)
\tag{FILTER-2}
$$

<a id="coupler"></a>
## 耦合器与分束器
理想 2x2 耦合器（功率分配 $k$）：

$$
\begin{bmatrix}E_{1,\mathrm{out}} \\ E_{2,\mathrm{out}}\end{bmatrix}=
\begin{bmatrix}\sqrt{k} & j\sqrt{1-k} \\ j\sqrt{1-k} & \sqrt{k}\end{bmatrix}
\begin{bmatrix}E_{1,\mathrm{in}} \\ E_{2,\mathrm{in}}\end{bmatrix}
\tag{CPL-1}
$$

非理想：
- 损耗：输出乘以 $10^{-L_{\mathrm{dB}}/20}$
- 分光比误差：$k \leftarrow k + \Delta k$
- 相位误差：一臂乘以 $e^{j\phi_{\mathrm{err}}}$

<a id="mzm"></a>
## 马赫-曾德尔调制器（MZM）
双臂干涉模型：

$$
E_{\mathrm{out}} = \frac{E_{\mathrm{in}}}{2}\left(e^{j\phi_1}+e^{j\phi_2}\right)
\tag{MZM-1}
$$

$$
\phi_1 = \phi_{\mathrm{bias}} + \pi\frac{V_1}{V_{\pi}},\quad
\phi_2 = -\phi_{\mathrm{bias}} + \pi\frac{V_2}{V_{\pi}}
\tag{MZM-2}
$$

定义共模与差模相位：

$$
\phi_c = \frac{\phi_1+\phi_2}{2},\quad \phi_d = \frac{\phi_1-\phi_2}{2}
$$

$$
E_{\mathrm{out}} = E_{\mathrm{in}}\,e^{j\phi_c}\cos(\phi_d)
\tag{MZM-3}
$$

推挽驱动（$V_1=+V/2,\;V_2=-V/2$）：

$$
\phi_d = \phi_{\mathrm{bias}} + \frac{\pi}{2}\frac{V}{V_{\pi}}
\tag{MZM-4}
$$

非理想：
- 臂损耗不平衡、相位失配导致消光比下降
- chirp：引入与 $V(t)$ 相关的额外相位项
- 驱动带宽限制
- 驱动噪声、偏置误差（与 PM 类似）

<a id="dpmzm"></a>
## 双并行 MZM（DPMZM）
DPMZM 由两个 MZM 并联，再通过相位器与合束器叠加：

$$
E_{\mathrm{out}} = \frac{E_I + j E_Q}{\sqrt{2}}
\tag{DPMZM-1}
$$

其中 $E_I, E_Q$ 为两个子 MZM 的输出。

I/Q 失衡（非理想）：
- 相位不平衡：$\phi_q \leftarrow \phi_q + \Delta\phi_{IQ}$
- 幅度不平衡：$E_Q \leftarrow E_Q \cdot 10^{-\Delta A_{\mathrm{dB}}/20}$

<a id="electrical"></a>
## 电信号源与增益
RF 源：

$$
v(t)=A\sin(2\pi f t+\phi)+V_{\mathrm{offset}}
\tag{ELEC-1}
$$

直流源：

$$
v(t)=V_{\mathrm{dc}}
\tag{ELEC-2}
$$

电增益：

$$
v_{\mathrm{out}}(t)=g\,v_{\mathrm{in}}(t)
\tag{ELEC-3}
$$

<a id="elec_splitter"></a>
## 电分路器（ElecSplitter）
理想分路：

$$
v_1(t)=v_{\mathrm{in}}(t),\quad v_2(t)=\alpha\,v_{\mathrm{in}}(t)
\tag{ELEC-4}
$$

<a id="polarization"></a>
## 偏振模型
Jones 形式：

$$
E_{\mathrm{out}} = J\,E_{\mathrm{in}}
$$

旋转器：

$$
R(\theta)=\begin{bmatrix}\cos\theta & -\sin\theta \\ \sin\theta & \cos\theta\end{bmatrix}
\tag{POL-1}
$$

PDL 示例：

$$
J = R(-\theta)\,\mathrm{diag}\left(10^{-\mathrm{PDL}/20},\;1\right)\,R(\theta)
\tag{POL-2}
$$

波片（相位延迟 $\delta$）：

$$
J = R(-\theta)\,\mathrm{diag}\left(e^{-j\delta/2},\;e^{j\delta/2}\right)\,R(\theta)
\tag{POL-3}
$$

<a id="pd"></a>
## 光电探测器（PD）
电流模型：

$$
i(t) = R\left(|E_x(t)|^2 + |E_y(t)|^2\right) + n(t)
\tag{PD-1}
$$

散粒噪声方差：

$$
\sigma_{\mathrm{shot}}^2 = 2 q I B
\tag{PD-2}
$$

热噪声方差：

$$
\sigma_{\mathrm{therm}}^2 = \frac{4 k_B T B}{R_L}
\tag{PD-3}
$$

噪声 $n(t)$ 通常以白噪声加入时域信号。

非理想补充：
- 暗电流：$i(t) \leftarrow i(t) + I_{\mathrm{dark}}$
- 响应度误差：$R \leftarrow R(1+\epsilon_R)$
- 饱和电流：$i(t) \leftarrow \min(i(t), I_{\mathrm{sat}})$
- 额外电流噪声：$i(t) \leftarrow i(t) + \sigma_I w(t)$

<a id="spectra"></a>
## OSA 与 ESA
光谱：

$$
S_{\mathrm{opt}}(f) = \left|\mathcal{F}\{E(t)\,w(t)\}\right|^2
\tag{SPEC-1}
$$

电谱：

$$
S_{\mathrm{elec}}(f) = \left|\mathcal{F}\{i(t)\,w(t)\}\right|^2
\tag{SPEC-2}
$$

dB 标度：

$$
S_{\mathrm{dB}} = 10\log_{10}\left(\frac{S}{S_\mathrm{ref}}\right)
\tag{SPEC-3}
$$

<a id="formula_index"></a>
## 公式索引

| 编号 | 说明 |
| --- | --- |
| LASER-1 | 激光器复包络 |
| LASER-2 | 激光线宽相位噪声 |
| LASER-3 | RIN 强度噪声 |
| PM-1 | PM 输出相位调制 |
| PM-2 | PM 相位-电压关系 |
| PM-3 | Bessel 展开 |
| LP-1 | 低通模型（RC） |
| ATT-1 | 光衰减器 |
| PS-1 | 相移器 |
| FIBER-1 | 光纤线性传输 |
| FIBER-2 | 光纤 PMD/双折射 |
| FIBER-3 | 光纤 Kerr 非线性 |
| FIBER-4 | 光纤 SSFM 分步 |
| FILTER-1 | 光学滤波器 |
| FILTER-2 | 光学滤波器相位 |
| CPL-1 | 2x2 耦合器 |
| MZM-1 | MZM 干涉输出 |
| MZM-2 | MZM 相位定义 |
| MZM-3 | MZM 余弦形式 |
| MZM-4 | 推挽驱动相位 |
| DPMZM-1 | DPMZM I/Q 合成 |
| ELEC-1 | RF 源 |
| ELEC-2 | DC 源 |
| ELEC-3 | 电增益 |
| ELEC-4 | 电分路 |
| POL-1 | 偏振旋转矩阵 |
| POL-2 | 偏振相关损耗 |
| POL-3 | 波片相位延迟 |
| PD-1 | PD 电流模型 |
| PD-2 | 散粒噪声 |
| PD-3 | 热噪声 |
| SPEC-1 | OSA 光谱 |
| SPEC-2 | ESA 电谱 |
| SPEC-3 | dB 标度 |

RBW/VBW 通过窗函数与平滑滤波实现。

## 参数与模型映射（实现对照）
以下列出关键参数在模型中的作用，便于参数与公式对应。

### Laser
- `power_dbm`：$P_0$，决定幅度 $\sqrt{P_0}$。
- `center_freq_hz`：载频 $f_0$。
- `phase0`：初始相位 $\phi_L(0)$。
- `linewidth_hz`：相位随机游走步长系数。
- `rin_db_per_hz`：强度噪声谱密度。
- `power_error_db`：$E \leftarrow E\cdot 10^{\Delta P/20}$。
- `freq_offset_hz`：$f_0 \leftarrow f_0+\Delta f$。
- `phase_noise_rms`：$\phi_L(t) \leftarrow \phi_L(t)+\sigma_\phi w(t)$。

### PM / MZM / DPMZM
- `Vpi`：半波电压，决定相位调制深度。
- `phi_bias` / `phi_bias_i` / `phi_bias_q`：偏置相位。
- `drive_mode`（MZM/DPMZM）：推挽或单臂驱动。
- `bandwidth_hz`：电带宽截止 $f_c$，0 表示不限制。
- `bandwidth_kind`：低通模型（rect/rc）。
- `loss_db`：输出乘以 $10^{-L/20}$。
- `vpi_error_pct`：$V_\pi \leftarrow V_\pi(1+\epsilon)$。
- `arm_ratio_db`：臂幅度不平衡系数。
- `phase_error`：相位失配项。
- `drive_noise_rms`：$V(t) \leftarrow V(t)+\sigma_V w(t)$。
- `bias_error_rad` / `bias_error_i` / `bias_error_q`：偏置误差。
- `iq_phase_error` / `iq_imbalance_db`（DPMZM）：I/Q 相位与幅度不平衡。

### Coupler / PhaseShifter / Attenuator
- `split_ratio`：功率分配 $k$。
- `split_ratio_error`：$k \leftarrow k+\Delta k$。
- `phase_error`：一臂附加相位误差。
- `loss_db`：输出乘以 $10^{-L/20}$。
- `phi`（PhaseShifter）：固定相移 $\phi$。

### OpticalFiber
- `length_m`：长度 $L$。
- `alpha_db_per_km`：损耗系数 $\alpha_{\mathrm{dB}}$，幅度乘以 $10^{-\alpha_{\mathrm{dB}}(L/1000)/20}$。
- `beta2_s2_per_m`：二阶色散 $\beta_2$。
- `beta3_s3_per_m`：三阶色散 $\beta_3$。
- `pmd_dgd_s`：偏振模色散 $\tau_{\mathrm{DGD}}$。
- `pmd_axis_angle_rad`：PMD 主轴角 $\theta$。
- `birefringence_phi_rad`：双折射相位延迟 $\phi_b$。
- `pmd_time_vary`：PMD 时变开关。
- `pmd_dgd_std_s` / `pmd_axis_std_rad` / `pmd_biref_std_rad`：DGD/主轴角/双折射漂移标准差。
- `pmd_corr_s`：漂移相关时间（0 表示独立更新）。
- `pmd_update_samples`：PMD 更新时间块长度。
- `nonlin_gamma_w_inv_m`：Kerr 系数 $\gamma$。
- `ssfm_steps`：SSFM 分步数。
- `ssfm_auto`：自动估计分步数（色散/非线性生效时）。
- `ssfm_max_phase_rad`：单步最大相位限制。
- `ssfm_length_frac`：长度尺度分步比例 $\eta$。
- `ssfm_auto_mode`：频宽估算方式（fft/fast）。
- `ssfm_min_steps` / `ssfm_max_steps`：自动分步上下限。

### OpticalFilter
- `kind`：滤波类型（lowpass/highpass/bandpass/bandstop）。
- `shape`：响应形状（rect/gaussian/butter）。
- `bandwidth_hz`：带宽或截止频率 $B$。
- `center_hz`：中心频率 $f_c$。
- `order`：Butterworth 阶数 $n$。
- `phase_mode`：相位模式（none/linear/quadratic/minimum）。
- `group_delay_s`：群时延 $\tau$。
- `gdd_s2`：群时延色散 $\beta_2$。

### PolarizationRotator / PolarizationPDL
- `angle_rad`：旋转角 $\theta$。
- `pdl_db`：偏振相关损耗 PDL（dB）。
- `axis_angle_rad`：PDL 主轴角 $\theta$。
- `loss_db`：公共损耗（幅度乘以 $10^{-L/20}$）。
- `retardance_rad`：波片相位延迟 $\delta$。
- `time_vary`：时变漂移开关。
- `angle_noise_std_rad` / `axis_noise_std_rad`：角度随机扰动标准差。
- `angle_drift_std_rad` / `axis_drift_std_rad`：角度漂移标准差。
- `pdl_noise_std_db` / `pdl_drift_std_db`：PDL 随机扰动与漂移标准差。
- `drift_corr_s`：漂移相关时间。
- `drift_update_samples`：漂移更新时间窗。

### PolarizationWaveplate / PolarizationController
- `retardance_rad` / `retardance1_rad..retardance3_rad`：波片相位延迟 $\delta$。
- `axis_angle_rad` / `angle1_rad..angle3_rad`：波片主轴角 $\theta$。
- `preset`：QHQ/H/Q 或自定义组合。
- `angle_noise_std_rad` / `retardance_noise_std_rad`：角度与相位延迟随机扰动（标准差）。
- `time_vary`：时变漂移开关。
- `axis_drift_std_rad` / `retardance_drift_std_rad`：角度与相位延迟漂移标准差。
- `drift_corr_s`：漂移相关时间。
- `drift_update_samples`：漂移更新时间窗。

### PD
- `responsivity`：$R$，电流 $i(t)=R|E|^2$。
- `bandwidth_hz`：电带宽截止 $f_c$，0 表示不限制。
- `bandwidth_kind`：低通模型（rect/rc）。
- `shot_noise` / `thermal_noise`：散粒/热噪声开关。
- `load_resistance` / `temperature_k`：热噪声参数。
- `dark_current`：$i(t) \leftarrow i(t)+I_{\mathrm{dark}}$。
- `responsivity_error_pct`：$R \leftarrow R(1+\epsilon)$。
- `saturation_current`：电流上限裁剪。
- `noise_current_rms`：额外白噪声电流。

### 电信号源与增益
- `RFSource`：$v(t)=A\sin(2\pi f t+\phi)+\mathrm{offset}$，支持频偏/幅相噪声/直流误差。
- `DCSource`：$v(t)=V_{\mathrm{dc}}+\Delta V + n(t)$。
- `ElecGain`：$v_{\mathrm{out}}=g\,v_{\mathrm{in}} + n(t)$。
- `ElecSplitter`：分路不平衡与输出噪声。
