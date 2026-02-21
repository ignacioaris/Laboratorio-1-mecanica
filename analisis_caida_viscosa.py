import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit

# ===============================
# Parámetros que puedes ajustar
# ===============================
ARCHIVO = "datos_caida.txt"

# Umbral para detectar "inicio de movimiento" (m/s).
# Para SRF04 suele funcionar 0.10–0.25 m/s según ruido.
V_START_TH = 0.15

# Suavizado Savitzky-Golay
WINDOW = 15   # debe ser impar y < len(data)
POLY = 3

g = 9.81

# ===============================
# 1) Cargar datos
# ===============================
df = pd.read_csv(ARCHIVO)
t_raw = df["time_ms"].values / 1000.0
y_raw = df["distance_m"].values

# ===============================
# 2) Suavizar y(t) para detectar movimiento con menos ruido
# ===============================
n = len(y_raw)
if n < 7:
    raise ValueError("Muy pocos datos para analizar. Captura más puntos.")

window = min(WINDOW, n - 1 if (n - 1) % 2 == 1 else n - 2)
if window < 7:
    window = 7 if n >= 7 else (n if n % 2 == 1 else n - 1)

y_s = savgol_filter(y_raw, window, POLY)

# ===============================
# 3) Detectar inicio de la caída y recortar
#    (usamos velocidad estimada sobre y suavizada)
# ===============================
v_tmp = np.gradient(y_s, t_raw)

# buscamos el primer índice donde |v| supera el umbral
idx_candidates = np.where(np.abs(v_tmp) > V_START_TH)[0]

if len(idx_candidates) == 0:
    raise ValueError(
        "No se detectó inicio de movimiento. "
        "Baja V_START_TH (ej. 0.08) o revisa si el objeto realmente se movió."
    )

i0 = idx_candidates[0]

# Recortamos desde un poquito antes para que v(0) ~ 0 quede mejor
pad = 2  # 2 muestras antes
i0 = max(i0 - pad, 0)

t = t_raw[i0:]
y = y_raw[i0:]
y_s = y_s[i0:]

# Re-centrar tiempo: ahora el primer dato es t=0
t = t - t[0]

# ===============================
# 4) Calcular velocidad experimental (suavizada) y aceleración experimental
# ===============================
v_exp = np.gradient(y_s, t)
a_exp = np.gradient(v_exp, t)

# Suaviza un poco a_exp para que no explote por ruido
a_exp_s = savgol_filter(a_exp, window, POLY) if len(a_exp) > window else a_exp

# ===============================
# 5) Ajuste del modelo cuadrático para v(t)
#    v(t) = vt * tanh(g t / vt)
# ===============================
def v_model(t, vt):
    return vt * np.tanh(g * t / vt)

# vt inicial: percentil alto de |v_exp| para evitar picos
vt_guess = np.nanpercentile(np.abs(v_exp), 90)
if vt_guess <= 0:
    vt_guess = 1.0

# Ajuste (limitamos vt a un rango razonable para estabilidad)
popt, _ = curve_fit(v_model, t, v_exp, p0=[vt_guess], bounds=(0.05, 20.0))
vt_fit = float(popt[0])

print(f"vt (ajustada) = {vt_fit:.3f} m/s")

# Aceleración del modelo cuadrático:
# a(t) = g(1 - tanh^2(g t / vt))
def a_model(t, vt):
    return g * (1 - np.tanh(g * t / vt)**2)

v_fit = v_model(t, vt_fit)
a_fit = a_model(t, vt_fit)

# ===============================
# 6) Gráficas
# ===============================
plt.figure(figsize=(12, 10))

# Distancia
plt.subplot(3, 1, 1)
plt.plot(t, y, alpha=0.35, label="y(t) crudo")
plt.plot(t, y_s, linewidth=2, label="y(t) suavizado")
plt.ylabel("Distancia (m)")
plt.legend()
plt.grid(True)

# Velocidad
plt.subplot(3, 1, 2)
plt.plot(t, v_exp, label="v(t) experimental (de y suavizado)")
plt.plot(t, v_fit, linewidth=2, label="v(t) modelo cuadrático")
plt.ylabel("Velocidad (m/s)")
plt.legend()
plt.grid(True)

# Aceleración
plt.subplot(3, 1, 3)
plt.plot(t, a_exp_s, alpha=0.6, label="a(t) experimental suavizada")
plt.plot(t, a_fit, linewidth=2, label="a(t) modelo cuadrático")
plt.ylabel("Aceleración (m/s²)")
plt.xlabel("Tiempo desde inicio de caída (s)")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

