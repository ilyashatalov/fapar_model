import numpy as np
import matplotlib.pyplot as plt


class FaparModel:
    Gb = 60
    Ge = 330
    etalonb = [-0.222, 0.064, -0.046, 0.025, -0.005, -0.002]
    etalonc = [-0.034, 0.013, 0.007, -0.025, 0.012, 0.004]

    def __init__(self, data):
        self.data = data

    # Parse DATA as list of (point[], scene name, DATE ACQUIRED, DOY, fapar mean, fapar sd)
    def draw_model(self):
        z_array = []
        H_array = []
        W_array = []

        for product in self.data:
            doy = product[3]
            value = product[4]
            sigma = product[5]
            t = ((doy - self.Gb) % 365) / ((self.Ge - self.Gb) % 365)  # Normalized DOY
            if t < 0 or t > 1 or sigma == -99.0000 or value < 1e-3 or sigma >= 2:
                continue
            elif sigma <= 3e-4:
                sigma = 1  # W = 1
            z_array.append(value)
            H_array.append([1, np.cos(2 * np.pi * t), np.cos(2 * 2 * np.pi * t), np.cos(3 * 2 * np.pi * t),
                            np.cos(4 * 2 * np.pi * t), np.cos(5 * 2 * np.pi * t), np.cos(6 * 2 * np.pi * t),
                            np.sin(4 * np.pi * t) - 2 * np.sin(2 * np.pi * t),
                            np.sin(6 * np.pi * t) - 3 * np.sin(2 * np.pi * t),
                            np.sin(8 * np.pi * t) - 4 * np.sin(2 * np.pi * t),
                            np.sin(10 * np.pi * t) - 5 * np.sin(2 * np.pi * t),
                            np.sin(12 * np.pi * t) - 6 * np.sin(2 * np.pi * t)])
            W_array.append(1 / sigma)
        H = np.array(H_array)
        Ht = np.transpose(H)
        W = np.diag(W_array)
        z = np.array(z_array)
        x = np.linalg.inv(Ht.dot(W).dot(H)).dot(Ht).dot(W).dot(z)
        a0 = x[0]
        # print("x:",x)
        b = x[1:7]
        m = 2
        c1 = 0
        cl = x[7:]
        for i in cl:
            c1 = c1 + i * m
            m = m + 1
        c = [-c1]
        for i in cl:
            c.append(i)
        F = []
        f = 0
        myFormattedListb = ['%.3f' % elem for elem in list(b)]
        myFormattedListc = ['%.3f' % elem for elem in list(c)]
        print("a0: ", a0)
        print("b 1-6:", myFormattedListb)
        print(" c1-6:", myFormattedListc)
        print("etalb:", self.etalonb)
        print("etalc:", self.etalonc)
        for t in np.linspace(0, 1, 365):
            for i in range(0, 6):
                j = i + 1
                f = f + (b[i] * np.cos(2 * np.pi * j * t) + c[i] * np.sin(2 * np.pi * j * t))
            F.append(a0 + f)
            f = 0
            j = 0
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.text(0, 1, "data from file")
        ax.text(0, 0.96, "a0: {}".format(a0))
        ax.text(0, 0.92, "b: {}".format(myFormattedListb))
        ax.text(0, 0.88, "c: {}".format(myFormattedListc))
        ax.axis([0, 365, 0, 1])
        ax.plot(F)
        plt.show()
        return fig




