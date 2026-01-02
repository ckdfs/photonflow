def main() -> None:
    import taichi as ti
    ti.init(arch=ti.gpu)
    print("PhotonFlow Engine Started on GPU!")

    x = ti.field(float, shape=())

    @ti.kernel
    def compute():
        x[None] = 1.0

    compute()
    print("Compute check passed.")


if __name__ == "__main__":
    main()
