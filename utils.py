import os

import matplotlib.pyplot as plt


def show_plot():
    """
    Conditionally show matplotlib plots based on environment variable.

    If HIDE_PLOTS environment variable is set, the plot will not be shown.
    Otherwise, plt.show() is called with block=False.
    """
    if not os.getenv("HIDE_PLOTS"):
        plt.show()
