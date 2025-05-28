import matplotlib.pyplot as plt

def plot_gastos_por_categoria(df):
    gastos = df[df["Tipo"] == "Gasto"]
    if gastos.empty:
        return None

    categoria = gastos.groupby("Categoría")["Monto"].sum().abs()
    fig, ax = plt.subplots()
    categoria.plot(kind="bar", ax=ax, color="tomato")
    ax.set_ylabel("Monto ($)")
    ax.set_title("Gastos por categoría")
    return fig